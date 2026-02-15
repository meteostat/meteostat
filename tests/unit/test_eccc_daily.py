"""
Test ECCC daily provider

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock

import pandas as pd

from meteostat.providers.eccc.daily import get_df, fetch
from meteostat.typing import Station
from meteostat.enumerations import Parameter


class TestGetDfEmptyFeatures:
    """Test get_df handles empty features from ECCC API"""

    @patch("meteostat.providers.eccc.daily.network_service")
    def test_get_df_returns_none_when_features_empty(self, mock_network):
        """When ECCC returns empty features list, get_df should return None instead of KeyError"""

        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023)

        assert result is None

    @patch("meteostat.providers.eccc.daily.network_service")
    def test_get_df_returns_none_when_no_features_key(self, mock_network):
        """When ECCC response has no features key at all, get_df should return None"""

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023)

        assert result is None


class TestFetchNoneMetaData:
    """Test fetch handles None meta_data from get_meta_data"""

    @patch("meteostat.providers.eccc.daily.get_meta_data")
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


class TestFetchMissingFields:
    """Test fetch handles missing required fields in meta_data"""

    @patch("meteostat.providers.eccc.daily.get_meta_data")
    def test_fetch_returns_none_when_climate_id_missing(self, mock_get_meta):
        """When meta_data is missing CLIMATE_IDENTIFIER, fetch should return None"""
        mock_get_meta.return_value = {
            "DLY_FIRST_DATE": "2020-01-01 00:00:00",
            "DLY_LAST_DATE": "2023-12-31 23:59:59",
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

    @patch("meteostat.providers.eccc.daily.get_meta_data")
    def test_fetch_returns_none_when_archive_dates_missing(self, mock_get_meta):
        """When meta_data is missing archive dates, fetch should return None"""
        mock_get_meta.return_value = {
            "CLIMATE_IDENTIFIER": "1234567",
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


class TestFetchMissingIdentifiers:
    """Test fetch handles missing identifiers"""

    def test_fetch_returns_none_when_no_national_identifier(self):
        """When station has no national identifier, fetch should return None"""

        req = MagicMock()
        req.station = Station(
            id="TEST01",
            name="Test Station",
            country="CA",
            latitude=45.0,
            longitude=-75.0,
            elevation=100,
            timezone="America/Toronto",
            identifiers={},
        )
        req.start = pd.Timestamp("2023-01-01")
        req.end = pd.Timestamp("2023-12-31")

        result = fetch(req)

        assert result is None

    def test_fetch_returns_none_when_no_start_date(self):
        """When request has no start date, fetch should return None"""

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
        req.start = None
        req.end = pd.Timestamp("2023-12-31")

        result = fetch(req)

        assert result is None

    def test_fetch_returns_none_when_no_end_date(self):
        """When request has no end date, fetch should return None"""

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
        req.end = None

        result = fetch(req)

        assert result is None


class TestGetDfWithData:
    """Test get_df with successful data retrieval"""

    @patch("meteostat.providers.eccc.daily.network_service")
    def test_get_df_processes_valid_data(self, mock_network):
        """Test that get_df properly processes valid ECCC response data"""

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "LOCAL_DATE": "2023-01-01",
                        "MAX_TEMPERATURE": 10.0,
                        "MEAN_TEMPERATURE": 5.0,
                        "MIN_TEMPERATURE": 0.0,
                        "SPEED_MAX_GUST": 50.0,
                        "TOTAL_PRECIPITATION": 10.0,
                        "SNOW_ON_GROUND": 20.0,
                        "TOTAL_SNOW": 5.0,
                    }
                }
            ]
        }
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567", 2023)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert Parameter.TMAX in result.columns
        assert result[Parameter.TMAX].iloc[0] == 10.0


class TestFetchWithValidData:
    """Test fetch with valid metadata and year range handling"""

    @patch("meteostat.providers.eccc.daily.get_df")
    @patch("meteostat.providers.eccc.daily.get_meta_data")
    def test_fetch_calculates_year_range_correctly(self, mock_get_meta, mock_get_df):
        """Test that fetch calculates the correct year range based on request and archive dates"""
        mock_get_meta.return_value = {
            "CLIMATE_IDENTIFIER": "1234567",
            "DLY_FIRST_DATE": "2020-01-01 00:00:00",
            "DLY_LAST_DATE": "2025-12-31 23:59:59",
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
