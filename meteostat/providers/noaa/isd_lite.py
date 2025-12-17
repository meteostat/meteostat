from datetime import datetime
from typing import Optional, Union
from urllib.error import HTTPError

from numpy import isnan
import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.core.cache import cache_service
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import ms_to_kmh, temp_dwpt_to_rhum

ISD_LITE_ENDPOINT = "https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/"
COLSPECS = [
    (0, 4),
    (5, 7),
    (8, 10),
    (11, 13),
    (13, 19),
    (19, 25),
    (25, 31),
    (31, 37),
    (37, 43),
    (43, 49),
    (49, 55),
]
COLUMN_NAMES = [
    "time",
    Parameter.TEMP,
    Parameter.DWPT,
    Parameter.PRES,
    Parameter.WDIR,
    Parameter.WSPD,
    Parameter.CLDC,
    Parameter.PRCP,
]


def map_sky_code(code: Union[int, str]) -> Optional[int]:
    """
    Only accept okta
    """
    return int(code) if not isnan(code) and int(code) >= 0 and int(code) <= 8 else None


def get_ttl(_usaf: str, _wban: str, year: int) -> int:
    """
    Get TTL based on year

    Current + previous year = one day
    Else = 30 days
    """
    current_year = datetime.now().year
    return TTL.DAY if current_year - year < 2 else TTL.MONTH


@cache_service.cache(get_ttl, "pickle")
def get_df(usaf: str, wban: str, year: int) -> Optional[pd.DataFrame]:
    if not usaf:
        return None

    filename = f"{usaf}-{wban if wban else '99999'}-{year}.gz"

    try:
        df = pd.read_fwf(
            f"{ISD_LITE_ENDPOINT}{year}/{filename}",
            parse_dates={"time": [0, 1, 2, 3]},
            na_values=["-9999", -9999],
            header=None,
            colspecs=COLSPECS,
            compression="gzip",
        )

        # Rename columns
        df.columns = COLUMN_NAMES

        # Adapt columns
        df[Parameter.TEMP] = df[Parameter.TEMP].div(10)
        df[Parameter.DWPT] = df[Parameter.DWPT].div(10)
        df[Parameter.PRES] = df[Parameter.PRES].div(10)
        df[Parameter.WSPD] = df[Parameter.WSPD].div(10).apply(ms_to_kmh)
        df[Parameter.CLDC] = df[Parameter.CLDC].apply(map_sky_code)
        df[Parameter.PRCP] = df[Parameter.PRCP].div(10)

        # Calculate humidity data
        # pylint: disable=unnecessary-lambda
        df[Parameter.RHUM] = df.apply(lambda row: temp_dwpt_to_rhum(row), axis=1)

        # Drop dew point column
        # pylint: disable=no-member
        df = df.drop(Parameter.DWPT, axis=1)

        # Set index
        df = df.set_index("time")

        # Round decimals
        return df.round(1)

    except HTTPError as error:
        if error.status == 404:
            logger.info(f"ISD Lite file not found: {filename}")
        else:
            logger.warning(
                f"Couldn't load ISD Lite file {filename} (status: {error.status})"
            )
        return None

    except Exception as error:
        logger.warning(error)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """ """
    if req.start is None or req.end is None:
        return None

    years = range(req.start.year, req.end.year + 1)
    data = tuple(
        map(
            lambda i: get_df(*i),
            (
                (
                    (
                        req.station.identifiers["usaf"]
                        if "usaf" in req.station.identifiers
                        else None
                    ),
                    (
                        req.station.identifiers["wban"]
                        if "wban" in req.station.identifiers
                        else None
                    ),
                    year,
                )
                for year in years
            ),
        )
    )

    return pd.concat(data) if len(data) and not all(d is None for d in data) else None
