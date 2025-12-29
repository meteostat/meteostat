from datetime import datetime
import meteostat as ms
from meteostat.providers.noaa.isd_lite import fetch
from meteostat.typing import ProviderRequest


def test_noaa_isd_lite():
    """
    It should load data from NOAA ISD Lite
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2022, 2, 1, 15),
        end=datetime(2022, 2, 1, 17),
        station=ms.Station(id="10637", identifiers={"usaf": "106370"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.RHUM],
    )
    df = fetch(query)

    assert len(df) > 1
    assert "temp" in df
    assert "rhum" in df
