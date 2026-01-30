from datetime import datetime
import meteostat as ms
from meteostat.providers.eccc.hourly import fetch
from meteostat.typing import ProviderRequest


def test_eccc_hourly():
    """
    It should load data from Environment and Climate Change Canada (hourly)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2020, 1, 1),
        end=datetime(2020, 12, 31),
        station=ms.Station(id="71508", identifiers={"national": "31688"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.RHUM],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "rhum" in df, "Relative humidity data is missing altogether."

    # Check that data contains reasonable number of non-missing entries.
    assert df["temp"].notna().sum() >= 100, "Insufficient temperature data returned."
    assert df["rhum"].notna().sum() >= 100, (
        "Insufficient relative humidity data returned."
    )
