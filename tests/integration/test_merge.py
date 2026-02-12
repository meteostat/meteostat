from datetime import datetime

import meteostat as ms
from meteostat.enumerations import Provider


def test_merge_providers(
    mock_stations_database,
    mock_dwd_hourly_fetch,
    mock_dwd_poi_fetch,
    mock_dwd_mosmix_fetch,
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


def test_merge_stations(mock_stations_database, mock_hourly_fetch):
    """
    It merges data from multiple weather stations correctly
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")
    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None
    ts_10637 = ms.hourly(
        station_10637,
        start,
        end,
    )
    ts_10635 = ms.hourly(
        station_10635,
        start,
        end,
    )
    ts_10532 = ms.hourly(
        station_10532,
        start,
        end,
    )
    ts_merged = ms.merge([ts_10637, ts_10635, ts_10532])
    df = ts_merged.fetch(sources=True)
    assert df is not None
    assert len(df) == 144
    assert df.index.get_level_values("station").unique().to_list() == [
        "10532",
        "10635",
        "10637",
    ]
    assert ts_merged.stations.index.unique().to_list() == ["10637", "10635", "10532"]
    assert ts_merged.start == start
    assert ts_merged.end == end


def test_merge_time(mock_stations_database, mock_hourly_fetch):
    """
    It merges data from multiple time ranges correctly
    """
    start1 = datetime(2024, 1, 10, 0, 0)
    end1 = datetime(2024, 1, 11, 23, 59)
    start2 = datetime(2024, 1, 12, 0, 0)
    end2 = datetime(2024, 1, 15, 23, 59)
    start3 = datetime(2024, 1, 20, 0, 0)
    end3 = datetime(2024, 1, 25, 23, 59)
    station_10637 = ms.stations.meta("10637")
    assert station_10637 is not None
    ts_1 = ms.hourly(
        station_10637,
        start1,
        end1,
    )
    ts_2 = ms.hourly(
        station_10637,
        start2,
        end2,
    )
    ts_3 = ms.hourly(
        station_10637,
        start3,
        end3,
    )
    ts_merged = ms.merge([ts_1, ts_2, ts_3])
    df = ts_merged.fetch(sources=True)
    assert df is not None
    assert len(df) == 288
    assert ts_merged.start == start1
    assert ts_merged.end == end3
