"""
Hourly Time Series Data

Access hourly time series data for one or multiple weather stations.
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
    Parameter.RHUM,
    Parameter.PRCP,
    Parameter.SNWD,
    Parameter.WDIR,
    Parameter.WSPD,
    Parameter.WPGT,
    Parameter.PRES,
    Parameter.TSUN,
    Parameter.CLDC,
    Parameter.COCO,
]


def hourly(
    station: str | Station | Point | List[str | Station | Point] | pd.DataFrame,
    start: Optional[datetime | date],
    end: Optional[datetime | date],
    timezone: Optional[str] = None,
    parameters: Optional[List[Parameter]] = None,
    providers: Optional[List[Provider]] = None,
):
    """
    Access hourly time series data.

    Parameters
    ----------
    station : str, Station, Point, List[str | Station | Point], pd.Index, pd.Series
        Weather station(s) or Point(s) to query data for. Can be a single station/point or a list.
        Points are converted to virtual stations with IDs like $0001, $0002, etc.
    start : datetime, date, optional
        Start date for the data query. If None, the earliest available date will be used.
    end : datetime, date, optional
        End date for the data query. If None, the latest available date will be used.
    timezone : str, optional
        Time zone for the data query. If None, UTC will be used.
    parameters : List[Parameter], optional
        List of parameters to include in the data query. Defaults to a set of common parameters.
    providers : List[Provider], optional
        List of data providers to use for the query. Defaults to the hourly provider.

    Returns
    -------
    TimeSeries
        A TimeSeries object containing the hourly data for the specified stations and parameters.
    """
    if parameters is None:
        parameters = DEFAULT_PARAMETERS
    if providers is None:
        providers = [Provider.HOURLY]

    req = Request(
        granularity=Granularity.HOURLY,
        providers=providers,
        parameters=parameters,
        station=parse_station(station),
        start=parse_time(start, timezone),
        end=parse_time(end, timezone, is_end=True),
        timezone=timezone,
    )

    return data_service.fetch(req)
