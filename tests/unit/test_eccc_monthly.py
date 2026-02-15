"""
Test ECCC monthly provider

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock

from meteostat.providers.eccc.monthly import get_df, fetch
from meteostat.typing import Station
from meteostat.enumerations import Parameter
import pandas as pd


class TestGetDfEmptyFeatures:
    """Test get_df handles empty features from ECCC API"""

    @patch("meteostat.providers.eccc.monthly.network_service")
    def test_get_df_returns_none_when_features_empty(self, mock_network):
        """When ECCC returns empty features list, get_df should return None instead of KeyError"""

        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567")

        assert result is None

    @patch("meteostat.providers.eccc.monthly.network_service")
    def test_get_df_returns_none_when_no_features_key(self, mock_network):
        """When ECCC response has no features key at all, get_df should return None"""

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567")

        assert result is None


class TestFetchNoneMetaData:
    """Test fetch handles None meta_data from get_meta_data"""

    @patch("meteostat.providers.eccc.monthly.get_meta_data")
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

        result = fetch(req)

        assert result is None


class TestFetchMissingFields:
    """Test fetch handles missing required fields in meta_data"""

    @patch("meteostat.providers.eccc.monthly.get_meta_data")
    def test_fetch_returns_none_when_climate_id_missing(self, mock_get_meta):
        """When meta_data is missing CLIMATE_IDENTIFIER, fetch should return None"""
        mock_get_meta.return_value = {}

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

        result = fetch(req)

        assert result is None


class TestGetDfWithData:
    """Test get_df with successful data retrieval"""

    @patch("meteostat.providers.eccc.monthly.network_service")
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
                        "TOTAL_PRECIPITATION": 100.0,
                        "DAYS_WITH_PRECIP_GE_1MM": 15,
                        "TOTAL_SNOWFALL": 50.0,
                    }
                }
            ]
        }
        mock_network.get.return_value = mock_response

        result = get_df.__wrapped__("1234567")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert Parameter.TEMP in result.columns
        assert result[Parameter.TEMP].iloc[0] == 5.0
