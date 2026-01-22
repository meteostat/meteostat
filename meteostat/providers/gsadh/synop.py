"""
GeoSphere Austria Data Hub SYNOP hourly data import routine

Get SYNOP (synoptic observation) hourly data for weather stations in Austria.

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
"""

from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.providers.gsadh.shared import API_BASE_URL, convert_wspd_ms_to_kmh
from meteostat.core.network import network_service


RESOURCE_ID = "synop-v1-1h"

# Mapping from GeoSphere Austria SYNOP parameter names to Meteostat parameters
PARAMETER_MAPPING: Dict[str, Parameter] = {
    "T": Parameter.TEMP,  # Air temperature (°C) - Lufttemperatur
    "Pp": Parameter.PRES,  # Air pressure (hPa) - Reduzierter Luftdruck
    "rel": Parameter.RHUM,  # Relative humidity (%) - Relative Feuchte
    "ff": Parameter.WSPD,  # Wind speed (m/s) - Windgeschwindigkeit
    "dd": Parameter.WDIR,  # Wind direction (°) - Windrichtung
    "RRR": Parameter.PRCP,  # Precipitation (mm) - Niederschlagsmenge
}

# Inverse mapping
METEOSTAT_TO_GSADH = {v: k for k, v in PARAMETER_MAPPING.items()}


@cache_service.cache(TTL.DAY, "pickle")
def get_data(
    station_id: str, parameters: list[str], start: datetime, end: datetime
) -> Optional[pd.DataFrame]:
    """
    Fetch SYNOP data from GeoSphere Austria Data Hub API
    """
    logger.debug(
        f"Fetching SYNOP hourly data for station '{station_id}' from {start} to {end}"
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
            f"Failed to fetch SYNOP data for station {station_id} (status: {response.status_code})"
        )
        return None

    try:
        data = response.json()

        if not data.get("features"):
            logger.info(f"No SYNOP data returned for station {station_id}")
            return None

        # Get timestamps array
        timestamps = data.get("timestamps")
        if not timestamps:
            logger.warning("No timestamps in SYNOP response")
            return None

        # Extract time series data from GeoJSON response
        # New API format has timestamps at top level and data as arrays
        feature = data["features"][0]
        props = feature.get("properties", {})
        params_data = props.get("parameters", {})

        if not params_data:
            logger.info(f"No parameter data returned for station {station_id}")
            return None

        # Build DataFrame from timestamps and parameter arrays
        df_dict = {}
        for param in parameters:
            if param in params_data:
                param_info = params_data[param]
                if "data" in param_info:
                    df_dict[param] = param_info["data"]

        if not df_dict:
            return None

        # Create DataFrame with timestamps as index
        df = pd.DataFrame(df_dict)
        df.index = pd.to_datetime(timestamps)
        df.index.name = "time"

        # Remove timezone info to match expected format (naive datetime)
        df.index = df.index.tz_localize(None)

        # Sort by time
        df = df.sort_index()

        return df

    except Exception as error:
        logger.warning(f"Error parsing SYNOP response: {error}", exc_info=True)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch SYNOP hourly data from GeoSphere Austria Data Hub
    """
    if "wmo" not in req.station.identifiers:
        return None

    station_id = req.station.identifiers["wmo"]

    # Map Meteostat parameters to GeoSphere Austria SYNOP parameters
    gsadh_params = []
    for param in req.parameters:
        if param in METEOSTAT_TO_GSADH:
            gsadh_params.append(METEOSTAT_TO_GSADH[param])

    if not gsadh_params:
        logger.info("No mappable parameters for GeoSphere Austria SYNOP data")
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

    # Round values
    df = df.round(1)

    return df
