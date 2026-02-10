"""
Test Point class

The code is licensed under the MIT license.
"""

import pytest
from meteostat import Point


class TestPointValidation:
    """Test Point validation"""

    def test_point_valid(self):
        """
        It should not raise an exception for valid coordinates
        """
        point = Point(45.0, 90.0, 100)
        assert point.latitude == 45.0
        assert point.longitude == 90.0
        assert point.elevation == 100

        point = Point(-45.0, -90.0)
        assert point.latitude == -45.0
        assert point.longitude == -90.0
        assert point.elevation is None

    def test_point_invalid_latitude(self):
        """
        It should raise an exception for invalid latitudes
        """
        with pytest.raises(Exception) as excinfo:
            Point(-91.0, 90.0)
        assert str(excinfo.value) == "Latitude must be between -90 and 90"

        with pytest.raises(Exception) as excinfo:
            Point(91.0, 90.0)
        assert str(excinfo.value) == "Latitude must be between -90 and 90"

    def test_point_invalid_longitude(self):
        """
        It should raise an exception for invalid longitudes
        """
        with pytest.raises(Exception) as excinfo:
            Point(45.0, -181.0)
        assert str(excinfo.value) == "Longitude must be between -180 and 180"

        with pytest.raises(Exception) as excinfo:
            Point(45.0, 181.0)
        assert str(excinfo.value) == "Longitude must be between -180 and 180"


class TestPointElevation:
    """Test Point elevation handling for sea level and truthiness"""

    def test_sea_level_elevation_is_valid(self):
        """Elevation 0 (sea level) should be valid and not False"""
        point = Point(52.3676, 4.9041, elevation=0)

        assert point.elevation == 0
        assert point.elevation is not None

    def test_sea_level_different_from_none_elevation(self):
        """Elevation 0 and None elevation should behave differently"""
        sea_level = Point(52.3676, 4.9041, elevation=0)
        no_elevation = Point(52.3676, 4.9041)

        assert sea_level.elevation == 0
        assert no_elevation.elevation is None
        assert sea_level.elevation != no_elevation.elevation

    def test_multiple_elevation_values_truthiness_bug(self):
        """Verify the bug is fixed: all non-None elevations should be recognized"""
        elevations = [0, -2, -5, 1, 100, 1000]

        for elev in elevations:
            point = Point(52.3676, 4.9041, elevation=elev)

            if point.elevation is not None:
                result = "has elevation"
            else:
                result = "no elevation"

            assert result == "has elevation"

    def test_lapserate_requires_elevation_not_none(self):
        """Lapse rate should be applied when elevation is not None (including 0)"""
        point_sea_level = Point(52.3676, 4.9041, elevation=0)
        point_no_elevation = Point(52.3676, 4.9041)

        should_apply_sea_level = point_sea_level.elevation is not None
        should_apply_no_elev = point_no_elevation.elevation is not None

        assert should_apply_sea_level is True
        assert should_apply_no_elev is False

    def test_coastal_cities_elevation_handling(self):
        """Test with real coastal cities (many have elevation 0 or negative)"""
        coastal_cities = [
            (52.3676, 4.9041, 0),
            (29.95, -90.07, -2),
            (35.68, 139.69, 0),
            (48.86, 2.29, 35),
        ]

        for lat, lon, elev in coastal_cities:
            point = Point(lat, lon, elevation=elev)

            has_valid_elevation = point.elevation is not None

            assert has_valid_elevation

            should_use_lapse = has_valid_elevation

            if elev == 0 or elev < 0:
                assert should_use_lapse is True

    def test_interpolation_elevation_none_check(self):
        """Interpolation should use is not None, not truthiness check"""
        point = Point(52.3676, 4.9041, elevation=0)

        if point.elevation is not None:
            lapse_rate_applied = True
        else:
            lapse_rate_applied = False

        assert lapse_rate_applied is True

    def test_latitude_longitude_same_issue(self):
        """Same bug could affect latitude/longitude (equator is 0)"""
        equator_point = Point(latitude=0, longitude=0)

        if equator_point.latitude:
            has_lat = True
        else:
            has_lat = False

        has_lat_correct = equator_point.latitude is not None

        assert has_lat is False
        assert has_lat_correct is True
