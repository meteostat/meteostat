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
