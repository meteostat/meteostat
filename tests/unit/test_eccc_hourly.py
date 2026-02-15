"""
Test ECCC hourly provider

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pandas as pd

from meteostat.providers.eccc.hourly import get_df, fetch
from meteostat.typing import Station
from meteostat.enumerations import Parameter


class TestGetDfEmptyFeatures:
    """Test get_df handles empty features from ECCC API (Bug 6)"""

    @patch("meteostat.providers.eccc.hourly.network_service")
    def test_get_df_returns_none_when_features_empty(self, mock_network):
        """When ECCC returns empty features list, get_df should return None instead of KeyError"""

        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023, "America/Toronto")

        assert result is None

    @patch("meteostat.providers.eccc.hourly.network_service")
    def test_get_df_returns_none_when_no_features_key(self, mock_network):
        """When ECCC response has no features key at all, get_df should return None"""

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023, "America/Toronto")

        assert result is None


class TestFetchNoneMetaData:
    """Test fetch handles None meta_data from get_meta_data (Bug 7)"""

    @patch("meteostat.providers.eccc.hourly.get_meta_data")
    def test_fetch_returns_none_when_meta_data_is_none(self, mock_get_meta):
        """When get_meta_data returns None, fetch should return None instead of AttributeError"""
        mock_get_meta.return_value = None

        req = MagicMock()
        req.station = Station(
            id="TEST01",
            name="Test Station",
            country="CA",
            latitude=45.0,
            longitude=-75.0,
            elevation=100,
            timezone="America/Toronto",
            identifiers={"national": "12345"},
        )
        req.start = pd.Timestamp("2023-01-01")
        req.end = pd.Timestamp("2023-12-31")

        result = fetch(req)

        assert result is None


class TestGetDfWithData:
    """Test get_df with successful data retrieval"""

    @patch("meteostat.providers.eccc.hourly.network_service")
    def test_get_df_processes_valid_data(self, mock_network):
        """Test that get_df properly processes valid ECCC response data"""

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "UTC_DATE": "2023-01-01T00:00:00Z",
                        "TEMP": 5.0,
                        "RELATIVE_HUMIDITY": 80,
                        "WIND_DIRECTION": 18,  # Will be multiplied by 10
                        "WIND_SPEED": 10.0,
                        "VISIBILITY": 5.0,  # Will be multiplied by 1000
                        "PRECIP_AMOUNT": 2.5,
                    }
                }
            ]
        }
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023, "America/Toronto")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        # Check that wind direction was multiplied by 10
        assert result[Parameter.WDIR].iloc[0] == 180
        # Check that visibility was multiplied by 1000
        assert result[Parameter.VSBY].iloc[0] == 5000


class TestFetchWithValidData:
    """Test fetch with valid metadata and year range handling"""

    @patch("meteostat.providers.eccc.hourly.get_df")
    @patch("meteostat.providers.eccc.hourly.get_meta_data")
    def test_fetch_handles_missing_timezone_field(self, mock_get_meta, mock_get_df):
        """Test that fetch returns None when timezone is missing"""
        mock_get_meta.return_value = {
            "CLIMATE_IDENTIFIER": "1234567",
            "HLY_FIRST_DATE": "2020-01-01 00:00:00",
            "HLY_LAST_DATE": "2023-12-31 23:59:59",
            # Missing TIMEZONE
        }

        req = MagicMock()
        req.station = Station(
            id="TEST01",
            name="Test Station",
            country="CA",
            latitude=45.0,
            longitude=-75.0,
            elevation=100,
            timezone="America/Toronto",
            identifiers={"national": "12345"},
        )
        req.start = pd.Timestamp("2023-01-01")
        req.end = pd.Timestamp("2023-12-31")

        result = fetch(req)

        assert result is None
        mock_get_df.assert_not_called()

    @patch("meteostat.providers.eccc.hourly.get_df")
    @patch("meteostat.providers.eccc.hourly.get_meta_data")
    def test_fetch_calculates_year_range_correctly(self, mock_get_meta, mock_get_df):
        """Test that fetch calculates the correct year range based on request and archive dates"""
        mock_get_meta.return_value = {
            "CLIMATE_IDENTIFIER": "1234567",
            "HLY_FIRST_DATE": "2020-01-01 00:00:00",
            "HLY_LAST_DATE": "2025-12-31 23:59:59",
            "TIMEZONE": "EST",
        }
        mock_get_df.return_value = None

        req = MagicMock()
        req.station = Station(
            id="TEST01",
            name="Test Station",
            country="CA",
            latitude=45.0,
            longitude=-75.0,
            elevation=100,
            timezone="America/Toronto",
            identifiers={"national": "12345"},
        )
        req.start = pd.Timestamp("2022-01-01")
        req.end = pd.Timestamp("2023-12-31")

        fetch(req)

        # Should call get_df for years 2022 and 2023
        assert mock_get_df.call_count == 2
