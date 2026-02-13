"""
Test ECCC hourly provider

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock

import pandas as pd

from meteostat.providers.eccc.hourly import get_df, fetch
from meteostat.typing import Station


class TestGetDfEmptyFeatures:
    """Test get_df handles empty features from ECCC API (Bug 6)"""

    @patch("meteostat.providers.eccc.hourly.network_service")
    @patch("meteostat.providers.eccc.hourly.cache_service")
    def test_get_df_returns_none_when_features_empty(self, mock_cache, mock_network):
        """When ECCC returns empty features list, get_df should return None instead of KeyError"""
        mock_cache.cache.return_value = lambda f: f

        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_network.get.return_value = mock_response

        result = get_df("1234567", 2023, "America/Toronto")

        assert result is None

    @patch("meteostat.providers.eccc.hourly.network_service")
    @patch("meteostat.providers.eccc.hourly.cache_service")
    def test_get_df_returns_none_when_no_features_key(self, mock_cache, mock_network):
        """When ECCC response has no features key at all, get_df should return None"""
        mock_cache.cache.return_value = lambda f: f

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_network.get.return_value = mock_response

        result = get_df("1234567", 2023, "America/Toronto")

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
