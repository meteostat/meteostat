"""
Test stations meta functionality

The code is licensed under the MIT license.
"""

from unittest.mock import patch

import pandas as pd

from meteostat.api.stations import Stations
from meteostat.typing import Station


class TestStationsMeta:
    """Test Stations.meta() method for handling non-existent stations"""

    def test_nonexistent_station_returns_none(self):
        """meta() should return None for a non-existent station ID"""
        stations = Stations()

        with patch.object(stations, "query", return_value=pd.DataFrame()):
            result = stations.meta("NONEXISTENT_STATION_12345")
            assert result is None

    def test_empty_string_station_returns_none(self):
        """meta("") should return None, not raise IndexError"""
        stations = Stations()

        with patch.object(stations, "query", return_value=pd.DataFrame()):
            result = stations.meta("")
            assert result is None

    def test_typo_station_returns_none(self):
        """User typo in station ID should return None"""
        stations = Stations()

        with patch.object(stations, "query", return_value=pd.DataFrame()):
            result = stations.meta("99999")
            assert result is None

    def test_valid_station_returns_station_object(self):
        """meta() should return Station object for valid station ID"""
        stations = Stations()

        station_df = pd.DataFrame(
            {
                "latitude": [50.0],
                "longitude": [8.0],
                "elevation": [100],
                "name": ["Test Station"],
            },
            index=pd.Index(["TEST123"], name="id"),
        )

        with patch.object(
            stations,
            "query",
            side_effect=[
                station_df,
                pd.DataFrame({"key": [], "value": []}),
            ],
        ):
            result = stations.meta("TEST123")

            assert isinstance(result, Station)
            assert result.id == "TEST123"
            assert result.latitude == 50.0
            assert result.longitude == 8.0
