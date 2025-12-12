"""
Test geo module

The code is licensed under the MIT license.
"""

import pytest

from meteostat.utils.geo import get_distance


class TestGetDistance:
    """Test geographical distance calculations"""

    def test_get_distance_same_point(self):
        """Test distance calculation for same point (should be 0)"""
        distance = get_distance(50.0, 8.0, 50.0, 8.0)
        assert distance == 0

    def test_get_distance_known_coordinates(self):
        """Test distance calculation with known coordinates"""
        # Distance between Frankfurt (50.1109, 8.6821) and Berlin (52.5200, 13.4050)
        # Approximate distance is 424 km
        distance = get_distance(50.1109, 8.6821, 52.5200, 13.4050)
        assert 420000 <= distance <= 430000  # ~424 km in meters

    def test_get_distance_equator_same_longitude(self):
        """Test distance calculation along equator"""
        # 1 degree at equator is approximately 111 km
        distance = get_distance(0.0, 0.0, 1.0, 0.0)
        assert 110000 <= distance <= 112000  # ~111 km in meters

    def test_get_distance_north_pole(self):
        """Test distance calculation near north pole"""
        distance = get_distance(89.0, 0.0, 90.0, 0.0)
        assert distance > 0
        assert distance < 125000  # Should be less than ~111 km due to pole convergence

    def test_get_distance_cross_meridian(self):
        """Test distance calculation crossing meridian"""
        # Distance from -170 to 170 longitude (20 degrees apart)
        distance = get_distance(0.0, -170.0, 0.0, 170.0)
        assert 2200000 <= distance <= 2250000  # ~222 km in meters

    def test_get_distance_negative_coordinates(self):
        """Test distance calculation with negative coordinates"""
        # New York to Los Angeles
        distance = get_distance(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3900000 <= distance <= 4200000  # ~4100 km in meters

    def test_get_distance_southern_hemisphere(self):
        """Test distance calculation in southern hemisphere"""
        # Sydney to Melbourne
        distance = get_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        assert 700000 <= distance <= 800000  # ~713 km in meters

    def test_get_distance_symmetry(self):
        """Test that distance calculation is symmetric"""
        distance1 = get_distance(50.0, 8.0, 52.0, 9.0)
        distance2 = get_distance(52.0, 9.0, 50.0, 8.0)
        assert distance1 == distance2

    def test_get_distance_small_distance(self):
        """Test distance calculation for very small distance"""
        # 0.01 degree at equator is approximately 1.1 km
        distance = get_distance(0.0, 0.0, 0.01, 0.0)
        assert 1000 <= distance <= 1200  # ~1100 meters

    def test_get_distance_one_km(self):
        """Test distance calculation to verify output is in meters"""
        # Approximate 0.009 degrees is about 1 km at equator
        distance = get_distance(0.0, 0.0, 0.009, 0.0)
        assert 900 <= distance <= 1100  # ~1000 meters
