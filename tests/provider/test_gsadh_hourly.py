from datetime import datetime
import meteostat as ms
from meteostat.providers.gsadh.hourly import fetch
from meteostat.typing import ProviderRequest


def test_gsadh_hourly():
    """
    It should load data from GeoSphere Austria Data Hub (hourly)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2024, 1, 1, 0),
        end=datetime(2024, 1, 1, 5),
        station=ms.Station(id="11035", identifiers={"geosphere_id": "11035"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 3, "Insufficient temperature data returned."
    assert df["prcp"].notna().sum() >= 0, "Precipitation data check failed."
