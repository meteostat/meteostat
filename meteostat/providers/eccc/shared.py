from typing import Optional

from meteostat.enumerations import TTL
from meteostat.core.cache import cache_service
from meteostat.core.network import network_service
from meteostat.core.logger import logger

import requests


ENDPOINT = "https://api.weather.gc.ca"


@cache_service.cache(TTL.WEEK)
def get_meta_data(station: str) -> Optional[dict]:
    try:
        response = network_service.get(
            f"{ENDPOINT}/collections/climate-stations/items",
            params={
                "STN_ID": station,
                "properties": ",".join(
                    [
                        "CLIMATE_IDENTIFIER",
                        "TIMEZONE",
                        "HLY_FIRST_DATE",
                        "HLY_LAST_DATE",
                        "DLY_FIRST_DATE",
                        "DLY_LAST_DATE",
                        "MLY_FIRST_DATE",
                        "MLY_LAST_DATE",
                    ]
                ),
                "f": "json",
            },
        )
    except requests.exceptions.ConnectionError:
        logger.warning(f"ECCC API connection failed for station {station}")
        return None

    if response.status_code == 200:
        data = response.json()
        try:
            return data["features"][0]["properties"]
        except (IndexError, KeyError):
            logger.info(f"ECCC climate identifier for station {station} not found")
    else:
        logger.warning(
            f"ECCC climate identifier for station {station} not found (status: {response.status_code})"
        )

    return None
