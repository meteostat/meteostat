"""
Test NetworkService retry and timeout configuration

The code is licensed under the MIT license.
"""

from unittest.mock import patch, MagicMock, call

import pytest
import requests

from meteostat.api.config import config
from meteostat.core.network import NetworkService


class TestNetworkServiceRetry:
    """Test NetworkService retry behavior"""

    def test_successful_request_on_first_attempt(self):
        """NetworkService should return response immediately on success"""
        service = NetworkService()

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            response = service.get("https://example.com")

            assert response.status_code == 200
            assert mock_get.call_count == 1

    def test_retries_on_server_error(self):
        """NetworkService should retry on 5xx status codes"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 2

            with patch("requests.get") as mock_get, patch("time.sleep"):
                error_response = MagicMock()
                error_response.status_code = 503

                success_response = MagicMock()
                success_response.status_code = 200

                mock_get.side_effect = [error_response, success_response]

                response = service.get("https://example.com")

                assert response.status_code == 200
                assert mock_get.call_count == 2
        finally:
            config.network_max_retries = original_retries

    def test_returns_5xx_response_after_max_retries_exceeded(self):
        """NetworkService should return the 5xx response after all retries are exhausted"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 2

            with patch("requests.get") as mock_get, patch("time.sleep"):
                error_response = MagicMock()
                error_response.status_code = 500

                mock_get.return_value = error_response

                response = service.get("https://example.com")

                assert response.status_code == 500
                # Should have tried max_retries + 1 times (1 initial + 2 retries)
                assert mock_get.call_count == 3
        finally:
            config.network_max_retries = original_retries

    def test_retries_on_connection_error(self):
        """NetworkService should retry on connection errors"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 2

            with patch("requests.get") as mock_get, patch("time.sleep"):
                success_response = MagicMock()
                success_response.status_code = 200

                mock_get.side_effect = [
                    requests.ConnectionError("Connection refused"),
                    success_response,
                ]

                response = service.get("https://example.com")

                assert response.status_code == 200
                assert mock_get.call_count == 2
        finally:
            config.network_max_retries = original_retries

    def test_raises_connection_error_after_max_retries(self):
        """NetworkService should raise last exception when all retries fail"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 1

            with patch("requests.get") as mock_get, patch("time.sleep"):
                mock_get.side_effect = requests.ConnectionError("Connection refused")

                with pytest.raises(requests.ConnectionError):
                    service.get("https://example.com")

                # 1 initial attempt + 1 retry = 2 calls
                assert mock_get.call_count == 2
        finally:
            config.network_max_retries = original_retries

    def test_no_retry_on_client_error(self):
        """NetworkService should not retry on 4xx status codes"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 3

            with patch("requests.get") as mock_get:
                not_found_response = MagicMock()
                not_found_response.status_code = 404
                mock_get.return_value = not_found_response

                response = service.get("https://example.com")

                assert response.status_code == 404
                assert mock_get.call_count == 1
        finally:
            config.network_max_retries = original_retries

    def test_exponential_backoff_between_retries(self):
        """NetworkService should use exponential backoff between retry attempts"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 3

            with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
                error_response = MagicMock()
                error_response.status_code = 500

                success_response = MagicMock()
                success_response.status_code = 200

                # Fail 3 times, succeed on 4th
                mock_get.side_effect = [
                    error_response,
                    error_response,
                    error_response,
                    success_response,
                ]

                service.get("https://example.com")

                # Backoff: 2^0=1, 2^1=2, 2^2=4
                assert mock_sleep.call_count == 3
                mock_sleep.assert_has_calls([call(1), call(2), call(4)])
        finally:
            config.network_max_retries = original_retries

    def test_response_closed_before_sleep_on_5xx(self):
        """NetworkService should close the 5xx response before sleeping to prevent connection leaks"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 2

            with patch("requests.get") as mock_get, patch("time.sleep"):
                error_response = MagicMock()
                error_response.status_code = 503

                success_response = MagicMock()
                success_response.status_code = 200

                mock_get.side_effect = [
                    error_response,
                    error_response,
                    success_response,
                ]

                service.get("https://example.com")

                # The two error responses should each have been closed before sleeping
                assert error_response.close.call_count == 2
        finally:
            config.network_max_retries = original_retries

    def test_uses_configurable_timeout(self):
        """NetworkService should use config.network_timeout for requests"""
        service = NetworkService()
        original_timeout = config.network_timeout

        try:
            config.network_timeout = 60

            with patch("requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                service.get("https://example.com")

                call_kwargs = mock_get.call_args.kwargs
                assert call_kwargs["timeout"] == 60
        finally:
            config.network_timeout = original_timeout

    def test_zero_retries_makes_single_attempt(self):
        """With network_max_retries=0, only one attempt should be made and 5xx is returned"""
        service = NetworkService()
        original_retries = config.network_max_retries

        try:
            config.network_max_retries = 0

            with patch("requests.get") as mock_get:
                error_response = MagicMock()
                error_response.status_code = 500
                mock_get.return_value = error_response

                response = service.get("https://example.com")

                assert response.status_code == 500
                assert mock_get.call_count == 1
        finally:
            config.network_max_retries = original_retries
