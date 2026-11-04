"""
Process GHCNh data

The code is licensed under the MIT license.
"""

from datetime import datetime
from typing import Optional
from urllib.error import HTTPError

import pandas as pd

from meteostat.enumerations import TTL, Frequency, Parameter
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.core.logger import logger
from meteostat.utils.conversions import ms_to_kmh
from meteostat.utils.data import enforce_freq, safe_concat

ENDPOINT = "https://noaa-ghcnh-pds.s3.amazonaws.com/hourly/access/by-year/"
COLUMN_NAMES = {
    "DATE": "time",
    "temperature": Parameter.TEMP,
    "dew_point_temperature": Parameter.DWPT,
    "relative_humidity": Parameter.RHUM,
    "sea_level_pressure": Parameter.PRES,
    "wind_direction": Parameter.WDIR,
    "wind_speed": Parameter.WSPD,
    "wind_gust": Parameter.WPGT,
    "precipitation": Parameter.PRCP,
    "snow_depth": Parameter.SNWD,
    "visibility": Parameter.VSBY,
}


def get_ttl(_station: str, year: int) -> int:
    """
    Get TTL based on year

    Current + previous year = one day
    Else = 30 days
    """
    current_year = datetime.now().year
    return TTL.DAY if current_year - year < 2 else TTL.MONTH


@cache_service.cache(get_ttl, "pickle")
def get_df(station: str, year: int) -> Optional[pd.DataFrame]:
    if not station:
        return None

    filename = f"GHCNh_{station}_{year}.psv"
    url = f"{ENDPOINT}{year}/psv/{filename}"

    try:
        df = pd.read_csv(  # type: ignore
            url,
            sep="|",
            usecols=list(COLUMN_NAMES.keys()),
        )

        # Rename columns
        df = df.rename(columns=COLUMN_NAMES)

        # Adapt columns
        df["time"] = pd.to_datetime(df["time"])
        # Wind direction is masked as 999 when winds are calm
        df[Parameter.WDIR] = df[Parameter.WDIR].where(df[Parameter.WDIR] <= 360)
        df[Parameter.WSPD] = df[Parameter.WSPD].apply(ms_to_kmh)
        df[Parameter.WPGT] = df[Parameter.WPGT].apply(ms_to_kmh)
        df[Parameter.SNWD] = df[Parameter.SNWD].div(10)
        df[Parameter.VSBY] = df[Parameter.VSBY].mul(1000)

        # Set time index and enforce hourly frequency
        df = df.set_index("time")
        df = enforce_freq(df, Frequency.HOURLY)

        return df.round(1)

    except HTTPError as error:
        if error.code == 404:
            logger.info(f"GHCNh file not found: {filename}")
        else:
            logger.warning(
                f"Couldn't load GHCNh file {filename} (status: {error.code})"
            )
        return None

    except Exception as error:
        logger.warning(error)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if req.start is None or req.end is None:
        return None

    ghcn_id = req.station.identifiers.get("ghcnh") or req.station.identifiers.get(
        "ghcn"
    )
    if not ghcn_id:
        return None

    years = range(req.start.year, req.end.year + 1)
    data = tuple(get_df(ghcn_id, year) for year in years)

    return safe_concat(data)
