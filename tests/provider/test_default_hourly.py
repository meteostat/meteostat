from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.meteostat.hourly import fetch
from meteostat.typing import ProviderRequest


def test_data_hourly():
    """
    Test default hourly data fetching.
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2020, 2, 1),
        end=datetime(2020, 2, 3),
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1, "No data returned for the specified date range."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."


def test_data_hourly_forecast():
    """
    Test that the default hourly provider returns data for the day seven days from now.
    """
    ms.config.cache_enable = False

    # Calculate the date seven days from now
    target_date = datetime.now() + timedelta(days=7)
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    end = datetime(target_date.year, target_date.month, target_date.day, 23, 59)

    query = ProviderRequest(
        start=start,
        end=end,
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    # Check if at least one datetime on the 7th day is present in the index
    time_index = df.index.get_level_values("time")
    has_target_date = any(t.date() == target_date.date() for t in time_index)
    assert has_target_date, f"No data found for the 7th day ({target_date.date()})"
