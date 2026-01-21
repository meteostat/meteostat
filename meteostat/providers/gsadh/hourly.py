"""
GeoSphere Austria Data Hub hourly data import routine

Get hourly climate data for weather stations in Austria.

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
"""

from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.providers.gsadh.shared import (
    API_BASE_URL,
    convert_wspd_ms_to_kmh,
    convert_tsun_h_to_min,
)
from meteostat.core.network import network_service


RESOURCE_ID = "klima-v2-1h"

# Mapping from GeoSphere Austria parameter names to Meteostat parameters
PARAMETER_MAPPING: Dict[str, Parameter] = {
    "tl": Parameter.TEMP,  # Air temperature (°C)
    "rr": Parameter.PRCP,  # Precipitation (mm)
    "p": Parameter.PRES,  # Air pressure (hPa)
    "ff": Parameter.WSPD,  # Wind speed (m/s)
    "dd": Parameter.WDIR,  # Wind direction (°)
    "rf": Parameter.RHUM,  # Relative humidity (%)
    "so_h": Parameter.TSUN,  # Sunshine duration (h)
    # Note: WPGT (wind gust), CLDC (cloud cover), SNWD (snow depth) may need different parameter names
    # from the API - these would need to be mapped once we have access to full API documentation
}

# Inverse mapping
METEOSTAT_TO_GSADH = {v: k for k, v in PARAMETER_MAPPING.items()}


@cache_service.cache(TTL.DAY, "pickle")
def get_data(
    station_id: str, parameters: list[str], start: datetime, end: datetime
) -> Optional[pd.DataFrame]:
    """
    Fetch data from GeoSphere Austria Data Hub API
    """
    logger.debug(
        f"Fetching hourly data for station '{station_id}' from {start} to {end}"
    )

    # Format dates as ISO 8601
    start_str = start.strftime("%Y-%m-%dT%H:%M")
    end_str = end.strftime("%Y-%m-%dT%H:%M")

    # Build URL
    url = f"{API_BASE_URL}/station/historical/{RESOURCE_ID}"

    # Make request
    response = network_service.get(
        url,
        params={
            "parameters": ",".join(parameters),
            "station_ids": station_id,
            "start": start_str,
            "end": end_str,
            "output_format": "geojson",
        },
    )

    if response.status_code != 200:
        logger.warning(
            f"Failed to fetch data for station {station_id} (status: {response.status_code})"
        )
        return None

    try:
        data = response.json()

        if not data.get("features"):
            logger.info(f"No data returned for station {station_id}")
            return None

        # Extract time series data from GeoJSON response
        records = []
        for feature in data["features"]:
            props = feature.get("properties", {})
            timestamp = props.get("time")
            if not timestamp:
                continue

            record = {"time": pd.to_datetime(timestamp)}
            for param in parameters:
                if param in props:
                    record[param] = props[param]

            records.append(record)

        if not records:
            return None

        df = pd.DataFrame(records)
        df = df.set_index("time")

        # Sort by time
        df = df.sort_index()

        return df

    except Exception as error:
        logger.warning(f"Error parsing response: {error}", exc_info=True)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch hourly data from GeoSphere Austria Data Hub
    """
    if "geosphere_id" not in req.station.identifiers:
        return None

    station_id = req.station.identifiers["geosphere_id"]

    # Map Meteostat parameters to GeoSphere Austria parameters
    gsadh_params = []
    for param in req.parameters:
        if param in METEOSTAT_TO_GSADH:
            gsadh_params.append(METEOSTAT_TO_GSADH[param])

    if not gsadh_params:
        logger.info("No mappable parameters for GeoSphere Austria hourly data")
        return None

    # Fetch data
    df = get_data(station_id, gsadh_params, req.start, req.end)

    if df is None or df.empty:
        return None

    # Rename columns to Meteostat parameter names
    rename_map = {}
    for gsadh_param, meteostat_param in PARAMETER_MAPPING.items():
        if gsadh_param in df.columns:
            rename_map[gsadh_param] = meteostat_param

    df = df.rename(columns=rename_map)

    # Convert units where necessary
    if Parameter.WSPD in df.columns:
        df[Parameter.WSPD] = df[Parameter.WSPD].apply(convert_wspd_ms_to_kmh)

    if Parameter.TSUN in df.columns:
        df[Parameter.TSUN] = df[Parameter.TSUN].apply(convert_tsun_h_to_min)

    # Round values
    df = df.round(1)

    return df
