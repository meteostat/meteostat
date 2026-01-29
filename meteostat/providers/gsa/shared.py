"""
Shared utilities for GeoSphere Austria Data Hub providers
"""

from typing import Optional

from meteostat.enumerations import TTL
from meteostat.core.cache import cache_service
from meteostat.core.network import network_service
from meteostat.core.logger import logger

API_BASE_URL = "https://dataset.api.hub.geosphere.at/v1"


@cache_service.cache(TTL.WEEK)
def get_station_metadata(resource_id: str) -> Optional[dict]:
    """
    Get metadata for a given resource including station information
    """
    url = f"{API_BASE_URL}/station/historical/{resource_id}/metadata"
    response = network_service.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        logger.warning(
            f"Failed to fetch metadata for {resource_id} (status: {response.status_code})"
        )
        return None


def find_station_by_id(metadata: dict, station_id: str) -> Optional[dict]:
    """
    Find a station in metadata by its ID
    """
    if not metadata or "stations" not in metadata:
        return None

    for station in metadata["stations"]:
        if str(station["id"]) == str(station_id):
            return station

    return None
