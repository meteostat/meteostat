"""
Test ECCC shared utilities

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock

from meteostat.providers.eccc.shared import get_meta_data
import requests


class TestGetMetaData:
    """Test get_meta_data function for fetching station metadata"""

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_properties_on_success(self, mock_network):
        """Test that get_meta_data returns station properties on successful API response"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "CLIMATE_IDENTIFIER": "1234567",
                        "TIMEZONE": "EST",
                        "HLY_FIRST_DATE": "2020-01-01 00:00:00",
                        "HLY_LAST_DATE": "2023-12-31 23:59:59",
                        "DLY_FIRST_DATE": "2020-01-01 00:00:00",
                        "DLY_LAST_DATE": "2023-12-31 23:59:59",
                        "MLY_FIRST_DATE": "2020-01-01 00:00:00",
                        "MLY_LAST_DATE": "2023-12-31 23:59:59",
                    }
                }
            ]
        }
        mock_network.get.return_value = mock_response

        result = get_meta_data.__wrapped__("TEST123")

        assert result is not None
        assert result["CLIMATE_IDENTIFIER"] == "1234567"
        assert result["TIMEZONE"] == "EST"

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_none_on_empty_features(self, mock_network):
        """Test that get_meta_data returns None when features list is empty"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"features": []}
        mock_network.get.return_value = mock_response

        result = get_meta_data.__wrapped__("TEST123")

        assert result is None

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_none_on_missing_properties(self, mock_network):
        """Test that get_meta_data returns None when response has no properties key"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"features": [{"no_properties": {}}]}
        mock_network.get.return_value = mock_response

        result = get_meta_data.__wrapped__("TEST123")

        assert result is None

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_none_on_404(self, mock_network):
        """Test that get_meta_data returns None on 404 status code"""

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_network.get.return_value = mock_response

        result = get_meta_data.__wrapped__("TEST123")

        assert result is None

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_none_on_connection_error(self, mock_network):
        """Test that get_meta_data returns None on connection error"""

        mock_network.get.side_effect = requests.exceptions.ConnectionError()

        result = get_meta_data.__wrapped__("TEST123")

        assert result is None

    @patch("meteostat.providers.eccc.shared.network_service")
    def test_get_meta_data_returns_none_on_timeout(self, mock_network):
        """Test that get_meta_data returns None on request timeout"""

        mock_network.get.side_effect = requests.exceptions.Timeout()

        result = get_meta_data.__wrapped__("TEST123")

        assert result is None
