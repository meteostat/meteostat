"""
Daily Time Series Data

Access daily time series data for one or multiple weather stations.
"""

from typing import List, Optional
from datetime import datetime, date

import pandas as pd

from meteostat.core.data import data_service
from meteostat.enumerations import Parameter, Provider, Granularity
from meteostat.typing import Station, Request
from meteostat.api.point import Point
from meteostat.utils.parsers import parse_station, parse_time

DEFAULT_PARAMETERS = [
    Parameter.TEMP,
    Parameter.TMIN,
    Parameter.TMAX,
    Parameter.RHUM,
    Parameter.PRCP,
    Parameter.SNWD,
    Parameter.WSPD,
    Parameter.WPGT,
    Parameter.PRES,
    Parameter.TSUN,
    Parameter.CLDC,
]


def daily(
    station: str | Station | Point | List[str | Station | Point] | pd.DataFrame,
    start: Optional[datetime | date],
    end: Optional[datetime | date],
    parameters: Optional[List[Parameter]] = None,
    providers: Optional[List[Provider]] = None,
):
    """
    Access daily time series data.

    Parameters
    ----------
    station : str, Station, Point, List[str | Station | Point], pd.Index, pd.Series
        Weather station(s) or Point(s) to query data for. Can be a single station/point or a list.
        Points are converted to virtual stations with IDs like $0001, $0002, etc.
    start : datetime, date, optional
        Start date for the data query. If None, the earliest available date will be used.
    end : datetime, date, optional
        End date for the data query. If None, the latest available date will be used.
    parameters : List[Parameter], optional
        List of parameters to include in the data query. Defaults to a set of common parameters.
    providers : List[Provider], optional
        List of data providers to use for the query. Defaults to the daily provider.

    Returns
    -------
    TimeSeries
        A TimeSeries object containing the daily data for the specified stations and parameters.
    """
    if parameters is None:
        parameters = DEFAULT_PARAMETERS
    if providers is None:
        providers = [Provider.DAILY]

    req = Request(
        granularity=Granularity.DAILY,
        providers=providers,
        parameters=parameters,
        station=parse_station(station),
        start=parse_time(start),
        end=parse_time(end, is_end=True),
    )

    return data_service.fetch(req)
