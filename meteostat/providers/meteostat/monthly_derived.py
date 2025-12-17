from typing import Optional

import numpy as np
import pandas as pd

from meteostat.enumerations import Parameter, Provider
from meteostat.api.daily import daily
from meteostat.typing import ProviderRequest
from meteostat.utils.data import aggregate_sources, reshape_by_source
from meteostat.utils.parsers import parse_month


def monthly_mean(group: pd.Series):
    """
    Calculate the monthly mean from a series of daily data
    """
    if group.isna().sum() > 3:
        return np.nan
    return group.interpolate(axis=0).mean()


def monthly_sum(group: pd.Series):
    """
    Calculate the monthly sum from a series of daily data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.sum()


def monthly_min(group: pd.Series):
    """
    Calculate the absolute minimum from a series of daily data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.interpolate(axis=0).min()


def monthly_max(group: pd.Series):
    """
    Calculate the absolute maximum from a series of daily data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.interpolate(axis=0).max()


# Available parameters with source column and aggregation method
PARAMETER_AGGS = {
    Parameter.TEMP: (Parameter.TEMP, monthly_mean),
    Parameter.TMIN: (Parameter.TMIN, monthly_mean),
    Parameter.TMAX: (Parameter.TMAX, monthly_mean),
    Parameter.TXMN: (Parameter.TMIN, monthly_min),
    Parameter.TXMX: (Parameter.TMAX, monthly_max),
    Parameter.PRCP: (Parameter.PRCP, monthly_sum),
    Parameter.PRES: (Parameter.PRES, monthly_mean),
    Parameter.TSUN: (Parameter.TSUN, monthly_sum),
}


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch daily weather data from Meteostat's central data
    repository and aggregate to monthly granularity
    """
    # Get all source columns
    source_cols = list(dict.fromkeys([PARAMETER_AGGS[p][0] for p in req.parameters]))

    # Get daily DataFrame
    ts_daily = daily(
        req.station.id,
        parse_month(req.start),
        parse_month(req.end, is_end=True),
        parameters=source_cols,
        providers=[Provider.DAILY],
    )

    df_daily = ts_daily.fetch(fill=True, sources=True)

    # If no daily data is available, exit
    if df_daily is None:
        return None

    # Create monthly aggregations
    df = pd.DataFrame()
    for parameter in req.parameters:
        [daily_param_name, agg_func] = PARAMETER_AGGS[parameter]
        df[parameter] = (
            df_daily[daily_param_name]
            .groupby(pd.Grouper(level="time", freq="MS"))
            .agg(agg_func)
        )
        df[f"{parameter}_source"] = (
            df_daily[f"{daily_param_name}_source"]
            .groupby(pd.Grouper(level="time", freq="MS"))
            .agg(aggregate_sources)
        )

    # Adjust DataFrame and add index
    df = df.round(1)
    df.index = pd.to_datetime(df.index.astype("datetime64").dt.date)  # type: ignore[union-attr]
    df.index.name = "time"

    # Return final DataFrame
    return reshape_by_source(df)
