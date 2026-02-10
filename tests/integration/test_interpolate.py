from datetime import datetime

import meteostat as ms


def test_interpolate(mock_stations_database, mock_hourly_fetch):
    """
    It interpolates data for a given point correctly
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")
    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None
    ts = ms.hourly(
        [
            station_10637,
            station_10635,
            station_10532,
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
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")
    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None
    ts = ms.hourly(
        [
            station_10637,
            station_10635,
            station_10532,
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


def test_interpolate_rounding(mock_stations_database, mock_hourly_fetch):
    """
    It rounds interpolated values to appropriate precision
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")
    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None
    ts = ms.hourly(
        [
            station_10637,
            station_10635,
            station_10532,
        ],
        start,
        end,
    )
    point = ms.Point(50.3167, 8.5, 320)
    test_interpolated = ms.interpolate(ts, point)
    df_interpolated = test_interpolated.fetch(sources=True)

    assert df_interpolated is not None

    # Check that temperature values are rounded to 1 decimal place
    if "temp" in df_interpolated.columns:
        for temp_val in df_interpolated["temp"].dropna():
            # Check that values have at most 1 decimal place
            # by converting to string and checking decimal places
            temp_str = str(float(temp_val))
            if "." in temp_str:
                decimal_part = temp_str.split(".")[1]
                assert len(decimal_part) <= 1, (
                    f"Temperature {temp_val} has more than 1 decimal place"
                )


def test_interpolate_categorical(mock_stations_database, mock_hourly_fetch):
    """
    It uses nearest neighbor for categorical parameters (WDIR, COCO)
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 11, 23, 59)
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")
    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None
    ts = ms.hourly(
        [
            station_10637,
            station_10635,
            station_10532,
        ],
        start,
        end,
    )
    point = ms.Point(50.3167, 8.5, 320)
    test_interpolated = ms.interpolate(ts, point)
    df_interpolated = test_interpolated.fetch(sources=True)

    assert df_interpolated is not None

    # Check that categorical parameters (WDIR, COCO) are integers (not interpolated)
    if "wdir" in df_interpolated.columns:
        for wdir_val in df_interpolated["wdir"].dropna():
            # WDIR should be an integer (UInt16) - check it's a whole number
            assert wdir_val == int(wdir_val), f"WDIR {wdir_val} is not an integer"

    if "coco" in df_interpolated.columns:
        for coco_val in df_interpolated["coco"].dropna():
            # COCO should be an integer (UInt8) - check it's a whole number
            assert coco_val == int(coco_val), f"COCO {coco_val} is not an integer"
