from datetime import datetime
import meteostat as ms
from meteostat.providers.noaa.ghcnh import fetch
from meteostat.typing import ProviderRequest


def test_noaa_ghcnh():
    """
    It should load data from NOAA GHCNh
    """
    query = ProviderRequest(
        start=datetime(2023, 1, 1, 0),
        end=datetime(2023, 1, 2, 0),
        station=ms.Station(id="72315", identifiers={"ghcn": "USW00003812"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.RHUM],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "rhum" in df, "Relative humidity data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 3, "Insufficient temperature data returned."
    assert df["rhum"].notna().sum() >= 3, (
        "Insufficient relative humidity data returned."
    )
