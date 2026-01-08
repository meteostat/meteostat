from datetime import datetime

import meteostat as ms


def test_interpolate(mock_stations_database, mock_hourly_fetch):
    """
    It interpolates data for a given point correctly
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    ts = ms.hourly(
        [
            ms.stations.meta("10637"),
            ms.stations.meta("10635"),
            ms.stations.meta("10532"),
        ],
        start,
        end,
    )
    df = ts.fetch()
    point = ms.Point(50.3167, 8.5, 320)
    test_interpolated = ms.interpolate(ts, point)
    df_interpolated = test_interpolated.fetch(sources=True)
    assert df_interpolated is not None
    assert len(df_interpolated) == 48
    assert (
        df_interpolated.iloc[0]["temp"]
        < df.xs("10637", level="station").iloc[0]["temp"]
    )
    assert (
        df_interpolated.iloc[0]["temp"]
        > df.xs("10635", level="station").iloc[0]["temp"]
    )
    # assert df_interpolated["temp"].mean() < df.xs("10637", level="station")["temp"].mean()
    # assert df_interpolated["temp"].mean() > df.xs("10635", level="station")["temp"].mean()


def test_interpolate_without_elevation(mock_stations_database, mock_hourly_fetch):
    """
    It interpolates data for a point without elevation
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    ts = ms.hourly(
        [
            ms.stations.meta("10637"),
            ms.stations.meta("10635"),
            ms.stations.meta("10532"),
        ],
        start,
        end,
    )
    # Create point without elevation (None)
    point = ms.Point(50.3167, 8.5)
    test_interpolated = ms.interpolate(ts, point)
    df_interpolated = test_interpolated.fetch(sources=True)
    assert df_interpolated is not None
    assert len(df_interpolated) == 48
