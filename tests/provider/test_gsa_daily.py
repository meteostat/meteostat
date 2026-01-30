from datetime import datetime
import meteostat as ms
from meteostat.providers.gsa.daily import fetch
from meteostat.typing import ProviderRequest


def test_gsa_daily():
    """
    It should load data from GeoSphere Austria Data Hub (daily)
    """
    query = ProviderRequest(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 5),
        station=ms.Station(id="11035", identifiers={"national": "105"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 3, "Insufficient temperature data returned."
    assert df["prcp"].notna().sum() >= 3, "Insufficient precipitation data returned."
