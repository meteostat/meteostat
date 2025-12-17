"""
The code is licensed under the MIT license.
"""

from datetime import datetime
from typing import Optional
from urllib.error import HTTPError

import pandas as pd

from meteostat.enumerations import TTL
from meteostat.core.logger import logger
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service


ENDPOINT = "https://bulk.meteostat.net/v2/raw/model/{year}/{station}.csv.gz"


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
    """
    Get CSV file from Meteostat and convert to DataFrame
    """
    file_url = ENDPOINT.format(station=station, year=str(year))

    try:
        df = pd.read_csv(file_url, sep=",", compression="gzip")
        time_cols = df.columns[0:4]
        df["time"] = pd.to_datetime(df[time_cols])
        return df.drop(time_cols, axis=1).set_index("time")

    except HTTPError as error:
        logger.info(f"Couldn't load MODEL file {file_url} (status: {error.status})")
        return None

    except Exception as error:
        logger.warning(error)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if req.start is None or req.end is None:
        return None

    years = range(req.start.year, req.end.year + 1)
    data = [get_df(req.station.id, year) for year in years]
    df = pd.concat(data) if len(data) and not all(d is None for d in data) else None
    if df is not None:
        df["source"] = (
            "dwd_mosmix" if "mosmix" in req.station.identifiers else "metno_forecast"
        )
        df.set_index(["source"], append=True, inplace=True)
    return df
