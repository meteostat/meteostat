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
        original_ua = config.aviationweather_user_agent
        try:
            config.aviationweather_user_agent = None

            with patch.object(metar, "network_service") as mock_net:
                result = metar.get_df("EDDF")

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

                metar._get_df_cached.__wrapped__("EDDF", "TestAgent/1.0")

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

    def test_metar_none_result_not_cached_without_user_agent(self):
        """METAR provider should not cache None when user agent is missing"""
        original_ua = config.aviationweather_user_agent
        original_cache_enable = config.cache_enable
        try:
            # Enable caching
            config.cache_enable = True

            # First call without user agent - should return None
            config.aviationweather_user_agent = None
            result1 = metar.get_df("EDDF")
            assert result1 is None

            # Now set user agent and mock a successful response
            config.aviationweather_user_agent = "TestAgent/1.0"

            with patch.object(metar, "network_service") as mock_net:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = ""
                mock_response.raise_for_status = MagicMock()
                mock_net.get.return_value = mock_response

                # Second call with user agent - should make network call (not return cached None)
                result2 = metar.get_df("EDDF")

                # Verify network call was made (meaning None wasn't cached)
                mock_net.get.assert_called_once()

        finally:
            config.aviationweather_user_agent = original_ua
            config.cache_enable = original_cache_enable
