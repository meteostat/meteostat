from datetime import datetime
import meteostat as ms
from meteostat.providers.gsa.synop import fetch
from meteostat.typing import ProviderRequest


def test_gsa_synop():
    """
    It should load data from GeoSphere Austria Data Hub (SYNOP hourly)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2024, 1, 1, 0),
        end=datetime(2024, 1, 1, 5),
        station=ms.Station(id="11035", identifiers={"wmo": "11035"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRES],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "pres" in df, "Pressure data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 3, "Insufficient temperature data returned."
    assert df["pres"].notna().sum() >= 3, "Insufficient pressure data returned."
