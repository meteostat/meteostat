from datetime import datetime
import meteostat as ms
from meteostat.providers.dwd.daily import fetch
from meteostat.typing import ProviderRequest


def test_dwd_daily():
    """
    It should load data from DWD Open Data (daily)
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2000, 2, 1, 15),
        end=datetime(2000, 2, 1, 17),
        station=ms.Station(id="10637", identifiers={"national": "01420"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1
    assert "temp" in df
    assert "prcp" in df
