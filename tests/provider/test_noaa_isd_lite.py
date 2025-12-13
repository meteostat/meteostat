from datetime import datetime
from meteostat import settings
from meteostat.providers.noaa.isd_lite import fetch
from meteostat.typing import QueryDict


def test_noaa_isd_lite():
    """
    It should load data from NOAA ISD Lite
    """
    settings["cache_enable"] = False

    query: QueryDict = {
        "start": datetime(2022, 2, 1, 15),
        "end": datetime(2022, 2, 1, 17),
        "station": {"id": "10637", "identifiers": {"usaf": "106370"}},
    }
    df = fetch(query)

    assert len(df) > 1
    assert "temp" in df
    assert "rhum" in df
