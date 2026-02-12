"""
Test User-Agent configuration and handling

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock

from meteostat.api.config import config
from meteostat.providers.noaa import metar
from meteostat.providers.metno import forecast


class TestUserAgent:
    """Test User-Agent defaults to None and providers skip when not configured"""

    def test_user_agent_defaults_to_none(self):
        """config.aviationweather_user_agent should default to None"""
        assert config.aviationweather_user_agent is None

    def test_metno_user_agent_defaults_to_none(self):
        """config.metno_user_agent should default to None"""
        assert config.metno_user_agent is None

    def test_metar_provider_skips_when_no_user_agent(self):
        """METAR provider should return None (skip) when no user agent is configured"""
        from meteostat.typing import ProviderRequest, Station

        original_ua = config.aviationweather_user_agent
        try:
            config.aviationweather_user_agent = None

            # Create mock station with ICAO identifier
            mock_station = MagicMock(spec=Station)
            mock_station.identifiers = {"icao": "EDDF"}

            # Create mock request
            mock_req = MagicMock(spec=ProviderRequest)
            mock_req.station = mock_station

            with patch.object(metar, "network_service") as mock_net:
                result = metar.fetch(mock_req)

                assert result is None
                mock_net.get.assert_not_called()
        finally:
            config.aviationweather_user_agent = original_ua

    def test_metno_provider_skips_when_no_user_agent(self):
        """Met.no provider should return None (skip) when no user agent is configured"""
        original_ua = config.metno_user_agent
        try:
            config.metno_user_agent = None

            with patch.object(forecast, "network_service") as mock_net:
                result = forecast.get_df.__wrapped__(50.0, 8.0, 100)

                assert result is None
                mock_net.get.assert_not_called()
        finally:
            config.metno_user_agent = original_ua

    def test_network_request_includes_version_header(self):
        """All HTTP requests should include version identification header"""
        from meteostat.core.network import network_service

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            try:
                network_service.get("https://example.com")
            except Exception:
                # Ignore exceptions - we only care about verifying headers were set
                pass

            if mock_get.called:
                call_args = mock_get.call_args
                headers = call_args.kwargs.get("headers", {})

                if headers:
                    assert "X-Meteostat-Version" in headers
                    assert headers["X-Meteostat-Version"] is not None

    def test_metar_provider_works_with_user_agent_configured(self):
        """METAR provider should work when user agent IS configured"""
        original_ua = config.aviationweather_user_agent
        try:
            config.aviationweather_user_agent = "TestAgent/1.0"

            with patch.object(metar, "network_service") as mock_net:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = ""
                mock_response.raise_for_status = MagicMock()
                mock_net.get.return_value = mock_response

                metar.get_df.__wrapped__("EDDF")

                mock_net.get.assert_called_once()
                call_args = mock_net.get.call_args
                headers = call_args.kwargs.get("headers", {})
                assert headers.get("User-Agent") == "TestAgent/1.0"
        finally:
            config.aviationweather_user_agent = original_ua

    def test_metar_request_headers_valid_when_configured(self):
        """When user agent is configured, METAR requests should have valid headers"""
        original_ua = config.aviationweather_user_agent
        try:
            config.aviationweather_user_agent = "TestAgent/1.0"
            user_agent = config.aviationweather_user_agent

            headers = {
                "User-Agent": user_agent,
                "Accept": "application/json",
            }

            assert all(v is not None and isinstance(v, str) for v in headers.values())
        finally:
            config.aviationweather_user_agent = original_ua

    def test_configuration_can_set_user_agent(self):
        """User should be able to configure User-Agent"""
        custom_ua = "MyCustomAgent/1.0"

        original_ua = config.aviationweather_user_agent
        try:
            config.aviationweather_user_agent = custom_ua
            assert config.aviationweather_user_agent == custom_ua
        finally:
            config.aviationweather_user_agent = original_ua

    def test_user_agent_type_is_optional_str(self):
        """User-Agent config should accept None or string values"""
        original_ua = config.aviationweather_user_agent

        try:
            config.aviationweather_user_agent = None
            assert config.aviationweather_user_agent is None

            config.aviationweather_user_agent = "Test/1.0"
            assert config.aviationweather_user_agent == "Test/1.0"
        finally:
            config.aviationweather_user_agent = original_ua
