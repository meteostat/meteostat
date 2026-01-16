from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.meteostat.daily import fetch
from meteostat.typing import ProviderRequest


def test_data_daily():
    """
    Test that the default daily provider returns data for three days ago.
    """
    ms.config.cache_enable = False

    # Calculate date three days ago
    three_days_ago = datetime.now() - timedelta(days=3)
    three_days_ago = datetime(three_days_ago.year, three_days_ago.month, three_days_ago.day)

    query = ProviderRequest(
        start=three_days_ago,
        end=three_days_ago,
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "source" in df.index.names, "Source data is missing altogether."

    # The provider will return all data, regardless of the requested date range.
    # Therefore, we are just testing if there is a reasonable amount of non-missing data.
    assert df["temp"].notna().sum() >= 1, "Insufficient temperature data returned."

    # Check if three days ago is present in the index
    assert three_days_ago in df.index.get_level_values("time"), f"Date three days ago ({three_days_ago}) is not in the index"
