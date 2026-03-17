"""
Network Service

The Network Service provides methods to send HTTP requests
considering the Meteostat configuration.
"""

import time
from typing import Optional

import requests

from meteostat import __version__
from meteostat.core.logger import logger
from meteostat.api.config import config


class NetworkService:
    """
    Network Service
    """

    @staticmethod
    def _process_headers(headers: dict) -> dict:
        """
        Process headers
        """

        headers["X-Meteostat-Version"] = __version__

        return headers

    def get(
        self,
        url: str,
        params=None,
        headers: Optional[dict] = None,
        stream: Optional[bool] = None,
    ) -> requests.Response:
        """
        Send a GET request using the Meteostat configuration, with retry on failure.

        4xx client error responses are returned directly without retrying.
        5xx server errors and connection errors trigger retries with exponential backoff.
        """
        if headers is None:
            headers = {}

        headers = self._process_headers(headers)

        max_retries = max(0, config.network_max_retries)

        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params,
                    headers=headers,
                    stream=stream,
                    proxies=config.network_proxies,
                    timeout=config.network_timeout,
                )
                # Return immediately for non-server-error responses (including 4xx)
                if response.status_code < 500:
                    return response
                logger.warning(
                    "Request to '%s' returned status %s (attempt %s/%s)",
                    url,
                    response.status_code,
                    attempt + 1,
                    max_retries + 1,
                )
                # For 5xx responses, retry with backoff; on final attempt, return the response
                if attempt == max_retries:
                    return response
                # Release connection before sleeping to avoid leaking file descriptors
                response.close()
            except requests.RequestException as exc:
                logger.warning(
                    "Request to '%s' failed (attempt %s/%s): %s",
                    url,
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                if attempt == max_retries:
                    raise

            time.sleep(2**attempt)

        # Unreachable: the loop always returns or raises on the final attempt
        raise RuntimeError("NetworkService.get() failed without raising an exception")  # pragma: no cover

    def get_from_mirrors(
        self,
        mirrors: list[str],
        params=None,
        headers: Optional[dict] = None,
        stream: Optional[bool] = None,
    ) -> Optional[requests.Response]:
        """
        Send a GET request to multiple mirrors using the Meteostat configuration
        """
        for mirror in mirrors:
            try:
                response = self.get(
                    mirror,
                    params=params,
                    headers=headers,
                    stream=stream,
                )
                if response.status_code == 200:
                    return response
            except requests.RequestException:
                logger.warning("Could not fetch data from '%s'", mirror)
                continue
        return None


network_service = NetworkService()
