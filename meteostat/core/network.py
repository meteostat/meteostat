"""
Network Service

The Network Service provides methods to send HTTP requests
considering the Meteostat configuration.
"""

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
        Send a GET request using the Meteostat configuration
        """
        if headers is None:
            headers = {}

        headers = self._process_headers(headers)

        return requests.get(
            url,
            params,
            headers=headers,
            stream=stream,
            proxies=config.network_proxies,
            timeout=30,
        )

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
