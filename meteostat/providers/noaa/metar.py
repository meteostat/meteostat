"""
The code is licensed under the MIT license.
"""

from typing import Any, Optional

import pandas as pd
from metar import Metar

from meteostat.core.logger import logger
from meteostat.api.config import config
from meteostat.enumerations import TTL, Frequency, Parameter
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import temp_dwpt_to_rhum
from meteostat.core.cache import cache_service
from meteostat.utils.data import enforce_freq
from meteostat.core.network import network_service


ENDPOINT = config.aviationweather_endpoint
USER_AGENT = config.aviationweather_user_agent
CLDC_MAP = {
    "FEW": 2,  # 1-2 octas
    "SCT": 4,  # 3-4 octas
    "BKN": 6,  # 5-7 octas
    "OVC": 8,  # 8 octas (fully overcast)
}
COCO_MAP = {
    "RA": 8,
    "SHRA": 17,
    "DZ": 7,
    "DZRA": 7,
    "FZRA": 10,
    "FZDZ": 10,
    "RASN": 12,
    "SN": 15,
    "SHSN": 21,
    "SG": 12,
    "IC": 12,
    "PL": 24,
    "GR": 24,
    "GS": 24,
    "FG": 5,
    "BR": 5,
    "MIFG": 5,
    "BCFG": 5,
    "HZ": 5,
    "TS": 25,
    "TSRA": 25,
    "PO": 27,
    "SQ": 27,
    "FC": 27,
    "SS": 27,
    "DS": 27,
}


def safe_get(obj: Optional[Any]) -> Optional[Any]:
    try:
        if obj is not None and hasattr(obj, "value"):
            return obj.value()
        return None
    except AttributeError:
        return None


def get_cldc(report: Metar.Metar) -> Optional[int]:
    """
    Get cloud cover (octas) from METAR report
    """
    try:
        cloud_cover = report.sky[0][0]
        return CLDC_MAP.get(cloud_cover)
    except IndexError:
        return None


def get_coco(report: Metar.Metar) -> Optional[int]:
    """
    Get weather condition code from METAR report
    """
    try:
        condition_code = "".join(
            [item for item in report.weather[0] if item is not None]
        )
        return COCO_MAP.get(condition_code)
    except IndexError:
        return None


def map_data(record):
    """
    Map METAR data to Meteostat column names
    """
    try:
        parsed_report = Metar.Metar(record)

        return {
            "time": parsed_report.time,
            Parameter.TEMP: safe_get(parsed_report.temp),
            Parameter.DWPT: safe_get(parsed_report.dewpt),
            Parameter.PRCP: safe_get(parsed_report.precip_1hr),
            Parameter.SNWD: safe_get(parsed_report.snowdepth),
            Parameter.WDIR: safe_get(parsed_report.wind_dir),
            Parameter.WSPD: safe_get(parsed_report.wind_speed),
            Parameter.WPGT: safe_get(parsed_report.wind_gust),
            Parameter.PRES: safe_get(parsed_report.press),
            Parameter.VSBY: safe_get(parsed_report.vis),
            Parameter.CLDC: get_cldc(parsed_report),
            Parameter.COCO: get_coco(parsed_report),
        }
    except Metar.ParserError:
        return None


@cache_service.cache(TTL.HOUR, "pickle")
def get_df(station: str) -> Optional[pd.DataFrame]:
    """
    Get CSV file from Meteostat and convert to DataFrame
    """
    url = ENDPOINT.format(station=station)

    if not USER_AGENT:
        logger.warning(
            "Consider specifying a unique user agent when querying the Aviation Weather Center's data API."
        )

    headers = {"User-Agent": USER_AGENT}

    response = network_service.get(url, headers=headers)

    # Raise an exception if the request was unsuccessful
    response.raise_for_status()

    # Parse the JSON content into a DataFrame
    data = [
        item for item in map(map_data, response.text.splitlines()) if item is not None
    ]

    # Return None if no data is available
    if not len(data):
        return None

    # Create DataFrame
    df = pd.DataFrame(data)

    # Return None if DataFrame is empty
    if df.empty:
        return None

    # Add RHUM column
    df[Parameter.RHUM] = df.apply(lambda row: temp_dwpt_to_rhum(row), axis=1)
    df[Parameter.RHUM] = df[Parameter.RHUM].round()

    # Set time index
    df = df.set_index(["time"])

    return enforce_freq(df, Frequency.HOURLY)


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if "icao" in req.station.identifiers:
        return get_df(req.station.identifiers["icao"])
