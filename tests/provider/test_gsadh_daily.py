from datetime import datetime
import meteostat as ms
from meteostat.providers.gsadh.daily import fetch
from meteostat.typing import ProviderRequest


def test_gsadh_daily():
    """
    It should load data from GeoSphere Austria Data Hub (daily)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 5),
        station=ms.Station(id="11035", identifiers={"geosphere_id": "11035"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.TMIN, ms.Parameter.TMAX],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "tmin" in df, "Minimum temperature data is missing altogether."
    assert "tmax" in df, "Maximum temperature data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 3, "Insufficient temperature data returned."
    assert df["tmin"].notna().sum() >= 3, "Insufficient minimum temperature data returned."
    assert df["tmax"].notna().sum() >= 3, "Insufficient maximum temperature data returned."
