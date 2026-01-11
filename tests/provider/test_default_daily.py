from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.meteostat.daily import fetch
from meteostat.typing import ProviderRequest


def test_data_daily():
    """
    Test default daily data fetching.
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2020, 2, 1),
        end=datetime(2020, 2, 3),
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TMIN, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1, "No data returned for the specified date range."
    assert "tmin" in df, "Minimum temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."


def test_data_daily_forecast():
    """
    Test that the default daily provider returns data for tomorrow's date.
    """
    ms.config.cache_enable = False

    # Calculate tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = datetime(tomorrow.year, tomorrow.month, tomorrow.day)

    query = ProviderRequest(
        start=tomorrow,
        end=tomorrow,
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    assert "temp" in df, "Temperature data is missing altogether."
    assert tomorrow in df.index.get_level_values("time"), f"Tomorrow's date ({tomorrow}) is not in the index"
