"""
The code is licensed under the MIT license.
"""

from datetime import datetime
from typing import Optional

import pandas as pd

from meteostat.providers.meteostat.shared import filter_model_data, handle_exceptions
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.api.config import config
from meteostat.utils.data import reshape_by_source

ENDPOINT = config.daily_endpoint


def get_ttl(_station: str, year: int) -> int:
    """
    Get TTL based on year

    Current + previous year = one day
    Else = 30 days
    """
    current_year = datetime.now().year
    return 60 * 60 * 24 if current_year - year < 2 else 60 * 60 * 24 * 30


@cache_service.cache(get_ttl, "pickle")
@handle_exceptions
def get_df(station: str, year: int) -> Optional[pd.DataFrame]:
    """
    Get CSV file from Meteostat and convert to DataFrame
    """
    file_url = ENDPOINT.format(station=station, year=str(year))

    df = pd.read_csv(file_url, sep=",", compression="gzip")

    time_cols = df.columns[0:3]
    df["time"] = pd.to_datetime(df[time_cols])
    df = df.drop(time_cols, axis=1).set_index("time")

    return reshape_by_source(df)


@filter_model_data
def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch daily weather data from Meteostat's central data repository
    """
    if req.start is None or req.end is None:
        return None

    # Get a list of relevant years
    years = range(req.start.year, req.end.year + 1)
    # Get list of annual DataFrames
    df_yearly = [get_df(req.station.id, year) for year in years]
    # Concatenate into a single DataFrame
    df = (
        pd.concat(df_yearly)
        if len(df_yearly) and not all(d is None for d in df_yearly)
        else None
    )
    return df
