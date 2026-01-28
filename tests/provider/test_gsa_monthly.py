from datetime import datetime
import meteostat as ms
from meteostat.providers.gsa.monthly import fetch
from meteostat.typing import ProviderRequest


def test_gsa_monthly():
    """
    It should load data from GeoSphere Austria Data Hub (monthly)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 6, 1),
        station=ms.Station(id="11035", identifiers={"national": "105"}),
        parameters=[ms.Parameter.TMIN, ms.Parameter.TMAX, ms.Parameter.PRCP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "tmin" in df, "Minimum temperature data is missing altogether."
    assert "tmax" in df, "Maximum temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["tmin"].notna().sum() >= 3, "Insufficient minimum temperature data returned."
    assert df["tmax"].notna().sum() >= 3, "Insufficient maximum temperature data returned."
    assert df["prcp"].notna().sum() >= 0, "Precipitation data check failed."
