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


def test_interpolate_sea_level_lapse_rate(mock_stations_database, mock_hourly_fetch):
    """
    Verify that lapse-rate correction is applied when elevation=0 (sea level).

    This integration test validates the fix in interpolate.py: the code must check
    `point.elevation is not None` rather than `if point.elevation` to handle
    elevation=0 correctly. Without this fix, elevation=0 would be treated as falsy
    and lapse-rate correction would be skipped.
    """
    start = datetime(2024, 1, 10, 0, 0)
    end = datetime(2024, 1, 10, 2, 0)  # Just 3 hours for quick test

    # Get stations with known elevations from fixtures
    # Station 10637: elevation 111m
    # Station 10532: elevation 186m
    # Station 10635: elevation 805m
    station_10637 = ms.stations.meta("10637")
    station_10635 = ms.stations.meta("10635")
    station_10532 = ms.stations.meta("10532")

    assert station_10637 is not None
    assert station_10635 is not None
    assert station_10532 is not None

    ts = ms.hourly(
        [station_10637, station_10635, station_10532],
        start,
        end,
    )

    # Create point at sea level (elevation=0)
    point_sea_level = ms.Point(50.3167, 8.5, elevation=0)

    # Interpolate WITHOUT lapse rate to get baseline
    ts_no_lapse = ms.interpolate(
        ts,
        point_sea_level,
        lapse_rate=None,  # Disable lapse rate
    )
    df_no_lapse = ts_no_lapse.fetch()

    # Interpolate WITH lapse rate enabled (default=6.5 C/km)
    ts_with_lapse = ms.interpolate(
        ts,
        point_sea_level,
        lapse_rate=6.5,
        lapse_rate_threshold=50,  # Apply if elevation diff >= 50m
    )
    df_with_lapse = ts_with_lapse.fetch()

    # Both should return data
    assert df_no_lapse is not None
    assert df_with_lapse is not None
    assert len(df_no_lapse) > 0
    assert len(df_with_lapse) > 0

    # Key assertion: temperatures with lapse-rate correction should be DIFFERENT
    # from those without. Since stations are at 111m, 186m, 805m (all above sea level),
    # the lapse-rate adjustment should make sea-level temperatures WARMER.
    #
    # If elevation=0 was incorrectly treated as falsy, both results would be identical.

    if "temp" in df_no_lapse.columns and "temp" in df_with_lapse.columns:
        temps_no_lapse = df_no_lapse["temp"].dropna()
        temps_with_lapse = df_with_lapse["temp"].dropna()

        assert len(temps_no_lapse) > 0, "Expected temperature data without lapse rate"
        assert len(temps_with_lapse) > 0, "Expected temperature data with lapse rate"

        # Calculate mean temperatures
        mean_no_lapse = temps_no_lapse.mean()
        mean_with_lapse = temps_with_lapse.mean()

        # With lapse rate correction at sea level (lower than stations),
        # temperatures should be warmer. The difference should be noticeable
        # (at least 0.5°C given the elevation differences).
        assert mean_with_lapse > mean_no_lapse, (
            f"Lapse-rate correction should make sea-level temps warmer. "
            f"Got mean_with_lapse={mean_with_lapse:.2f}, "
            f"mean_no_lapse={mean_no_lapse:.2f}"
        )

        # Verify the difference is significant (at least 0.3°C)
        # With stations at ~111-805m and lapse rate 6.5°C/km, we expect
        # roughly 0.7-5.2°C difference
        temp_diff = mean_with_lapse - mean_no_lapse
        assert temp_diff > 0.3, (
            f"Temperature difference {temp_diff:.2f}°C is too small. "
            f"Expected at least 0.3°C with lapse-rate correction."
        )
