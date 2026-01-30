from datetime import datetime
import meteostat as ms
from meteostat.providers.dwd.hourly import fetch
from meteostat.typing import ProviderRequest


def test_dwd_hourly():
    """
    It should load data from DWD Open Data (hourly)
    """
    query = ProviderRequest(
        start=datetime(2000, 2, 1, 15),
        end=datetime(2000, 2, 1, 17),
        station=ms.Station(id="10637", identifiers={"national": "01420"}),
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
