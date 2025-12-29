from datetime import datetime
import meteostat as ms
from meteostat.providers.meteostat.daily import fetch
from meteostat.typing import ProviderRequest


def test_data_daily():
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2020, 2, 1),
        end=datetime(2020, 2, 3),
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TMIN, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1
    assert "tmin" in df
    assert "prcp" in df
