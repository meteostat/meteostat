"""
GeoSphere Austria Data Hub monthly data import routine

Get monthly climate data for weather stations in Austria.

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
"""

from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.api.config import config
from meteostat.core.network import network_service
from meteostat.utils.conversions import (
    hours_to_minutes,
    ms_to_kmh,
    percentage_to_okta,
    pres_to_msl,
)


RESOURCE_ID = "klima-v2-1m"

# Mapping from GeoSphere Austria parameter names to Meteostat parameters
# See: https://dataset.api.hub.geosphere.at/v1/station/historical/klima-v2-1m/metadata
PARAMETER_MAPPING: Dict[str, Parameter] = {
    "tl_mittel": Parameter.TEMP,  # Mean air temperature (°C) - Lufttemperatur 2m Mittelwert
    "tlmin": Parameter.TXMN,  # Minimum air temperature (°C) - Lufttemperatur 2m Minimalwert
    "tlmax": Parameter.TXMX,  # Maximum air temperature (°C) - Lufttemperatur 2m Maximalwert
    "tlmin_mittel": Parameter.TMIN,  # Mean minimum air temperature (°C) - Lufttemperatur 2m Mittelwert der Minima
    "tlmax_mittel": Parameter.TMAX,  # Mean maximum air temperature (°C) - Lufttemperatur 2m Mittelwert der Maxima
    "rf_mittel": Parameter.RHUM,  # Mean relative humidity (%) - Relative Feuchte Mittelwert
    "rr": Parameter.PRCP,  # Precipitation sum (mm) - Niederschlag Summe der 24h-Summen
    "vv_mittel": Parameter.WSPD,  # Mean wind speed (m/s) - Windgeschwindigkeit Mittelwert
    "p": Parameter.PRES,  # Mean air pressure (hPa) - Luftdruck Mittelwert
    "so_h": Parameter.TSUN,  # Sunshine duration (h) - Sonnenscheindauer
    "bewm_mittel": Parameter.CLDC,  # Mean cloud cover (%) - Bedeckung Mittelwert
}

# Inverse mapping
METEOSTAT_TO_GSA = {v: k for k, v in PARAMETER_MAPPING.items()}


@cache_service.cache(TTL.MONTH, "pickle")
def get_data(
    station_id: str,
    elevation: int | None,
    parameters: list[str],
    start: datetime,
    end: datetime,
) -> Optional[pd.DataFrame]:
    """
    Fetch data from GeoSphere Austria Data Hub API
    """
    logger.debug(
        f"Fetching monthly data for station '{station_id}' from {start} to {end}"
    )

    # Format dates as ISO 8601 (full date for monthly data)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    # Build URL
    url = f"{config.gsa_api_base_url}/station/historical/{RESOURCE_ID}"

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
            f"Failed to fetch monthly data for station {station_id} (status: {response.status_code}): {response.json()}",
        )
        return None

    try:
        data = response.json()

        if not data.get("features"):
            logger.info(f"No monthly data returned for station {station_id}")
            return None

        # Get timestamps array
        timestamps = data.get("timestamps")
        if not timestamps:
            logger.warning("No timestamps in monthly response")
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

        # Rename columns to Meteostat parameter names
        rename_map = {}
        for gsadh_param, meteostat_param in PARAMETER_MAPPING.items():
            if gsadh_param in df.columns:
                rename_map[gsadh_param] = meteostat_param

        df = df.rename(columns=rename_map)

        # Convert units where necessary
        if Parameter.WSPD in df.columns:
            df[Parameter.WSPD] = df[Parameter.WSPD].apply(ms_to_kmh)

        if Parameter.TSUN in df.columns:
            df[Parameter.TSUN] = df[Parameter.TSUN].apply(hours_to_minutes)

        if Parameter.CLDC in df.columns:
            # Convert cloud cover from % to okta
            df[Parameter.CLDC] = df[Parameter.CLDC].apply(percentage_to_okta)

        if Parameter.PRES in df.columns:
            df[Parameter.PRES] = df.apply(
                lambda row: pres_to_msl(row, elevation), axis=1
            )

        # Round values
        df = df.round(1)

        return df

    except Exception as error:
        logger.warning(f"Error parsing monthly response: {error}", exc_info=True)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch monthly data from GeoSphere Austria Data Hub
    """
    if "national" not in req.station.identifiers:
        return None

    station_id = req.station.identifiers["national"]

    # Map Meteostat parameters to GeoSphere Austria parameters
    gsa_params = []
    for param in req.parameters:
        if param in METEOSTAT_TO_GSA:
            gsa_params.append(METEOSTAT_TO_GSA[param])

    if not gsa_params:
        logger.info("No mappable parameters for GeoSphere Austria monthly data")
        return None

    # Fetch data
    df = get_data(station_id, req.station.elevation, gsa_params, req.start, req.end)

    if df is None or df.empty:
        return None

    return df
