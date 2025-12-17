from datetime import datetime

import meteostat as ms
from meteostat.enumerations import Provider

def test_merge_providers(
    mock_station, mock_dwd_hourly_fetch, mock_dwd_poi_fetch, mock_dwd_mosmix_fetch
):
    """
    It merges data from multiple providers correctly
    """
    start = datetime(2025, 12, 1, 0, 0)
    end = datetime(2025, 12, 18, 23, 59)
    ts_dwd_hourly = ms.hourly(
        "10637",
        start,
        end,
        providers=[ms.Provider.DWD_HOURLY],
    )
    ts_dwd_poi = ms.hourly(
        "10637",
        start,
        end,
        providers=[ms.Provider.DWD_POI],
    )
    ts_dwd_mosmix = ms.hourly(
        "10637",
        start,
        end,
        providers=[ms.Provider.DWD_MOSMIX],
    )
    ts_merged = ms.merge([ts_dwd_hourly, ts_dwd_poi, ts_dwd_mosmix])
    df = ts_merged.fetch(sources=True)
    assert df is not None
    assert len(df) == 432
    assert df.iloc[0]["temp_source"] == Provider.DWD_HOURLY
    assert df.iloc[380]["temp_source"] == Provider.DWD_POI
    assert df.iloc[431]["temp_source"] == Provider.DWD_MOSMIX