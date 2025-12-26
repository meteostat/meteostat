"""
Test parsers module

The code is licensed under the MIT license.
"""

from meteostat import Point
from meteostat.typing import Station
from meteostat.utils.parsers import parse_station, _point_to_station


class TestPointToStation:
    """Test point to station conversion"""

    def test_point_to_station(self):
        """
        Test converting a Point to a virtual Station
        """
        point = Point(50.110924, 8.682127, 112)
        station = _point_to_station(point, 1)

        assert station.id == "$0001"
        assert station.latitude == 50.110924
        assert station.longitude == 8.682127
        assert station.elevation == 112

    def test_point_to_station_multiple(self):
        """
        Test converting multiple Points to virtual Stations
        """
        point1 = Point(50.0, 8.0, 100)
        point2 = Point(51.0, 9.0, 200)
        point3 = Point(52.0, 10.0, 300)

        station1 = _point_to_station(point1, 1)
        station2 = _point_to_station(point2, 2)
        station3 = _point_to_station(point3, 3)

        assert station1.id == "$0001"
        assert station2.id == "$0002"
        assert station3.id == "$0003"

    def test_point_to_station_without_elevation(self):
        """
        Test converting a Point without elevation to a virtual Station
        """
        point = Point(50.0, 8.0)
        station = _point_to_station(point, 1)

        assert station.id == "$0001"
        assert station.latitude == 50.0
        assert station.longitude == 8.0
        assert station.elevation is None


class TestParseStation:
    """Test parse_station function"""

    def test_parse_station_with_point(self):
        """
        Test parse_station with a single Point (returns single Station)
        """
        point = Point(50.110924, 8.682127, 112)
        result = parse_station(point)

        assert isinstance(result, Station)
        assert result.id == "$0001"
        assert result.latitude == 50.110924
        assert result.longitude == 8.682127
        assert result.elevation == 112

    def test_parse_station_with_station(self):
        """
        Test parse_station with a Station object (returns single Station)
        """
        station = Station(id="TEST01", latitude=50.0, longitude=8.0, elevation=100)
        result = parse_station(station)

        assert isinstance(result, Station)
        assert result is station

    def test_parse_station_with_mixed_list(self):
        """
        Test parse_station with a mixed list of Points and Stations (returns list)
        """
        point1 = Point(50.0, 8.0, 100)
        point2 = Point(51.0, 9.0, 200)
        station1 = Station(id="TEST01", latitude=52.0, longitude=10.0, elevation=300)

        result = parse_station([point1, station1, point2])

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].id == "$0001"
        assert result[0].latitude == 50.0
        assert result[1] is station1
        assert result[2].id == "$0002"
        assert result[2].latitude == 51.0

    def test_parse_station_with_point_list(self):
        """
        Test parse_station with a list of Points (returns list)
        """
        point1 = Point(50.0, 8.0, 100)
        point2 = Point(51.0, 9.0, 200)
        point3 = Point(52.0, 10.0, 300)

        result = parse_station([point1, point2, point3])

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].id == "$0001"
        assert result[1].id == "$0002"
        assert result[2].id == "$0003"
        assert result[0].latitude == 50.0
        assert result[1].latitude == 51.0
        assert result[2].latitude == 52.0

    def test_parse_station_list_with_one_item(self):
        """
        Test parse_station with a list containing a single Station (returns list)
        """
        station = Station(id="TEST01", latitude=50.0, longitude=8.0, elevation=100)
        result = parse_station([station])

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] is station
