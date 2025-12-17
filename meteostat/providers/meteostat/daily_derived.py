from typing import Optional

import numpy as np
import pandas as pd

from meteostat.enumerations import Parameter, Provider
from meteostat.api.hourly import hourly
from meteostat.typing import ProviderRequest
from meteostat.utils.data import aggregate_sources, reshape_by_source


def daily_mean(group: pd.Series):
    """
    Calculate the daily mean from a series of hourly data
    """
    if group.isna().sum() > 3:
        return np.nan
    return group.interpolate(axis=0).mean()


def daily_min(group: pd.Series):
    """
    Calculate the daily minimum from a series of hourly data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.min()


def daily_max(group: pd.Series):
    """
    Calculate the daily maximum from a series of hourly data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.max()


def daily_sum(group: pd.Series):
    """
    Calculate the daily sum from a series of hourly data
    """
    if group.isna().sum() > 0:
        return np.nan
    return group.sum()


# Available parameters with source column and aggregation method
PARAMETER_AGGS = {
    Parameter.TEMP: (Parameter.TEMP, daily_mean),
    Parameter.TMIN: (Parameter.TEMP, daily_min),
    Parameter.TMAX: (Parameter.TEMP, daily_max),
    Parameter.RHUM: (Parameter.RHUM, daily_mean),
    Parameter.DWPT: (Parameter.DWPT, daily_mean),
    Parameter.PRCP: (Parameter.PRCP, daily_sum),
    Parameter.SNWD: (Parameter.SNWD, daily_max),
    Parameter.WSPD: (Parameter.WSPD, daily_mean),
    Parameter.WPGT: (Parameter.WPGT, daily_max),
    Parameter.PRES: (Parameter.PRES, daily_mean),
    Parameter.TSUN: (Parameter.TSUN, daily_sum),
    Parameter.CLDC: (Parameter.CLDC, daily_mean),
}


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch hourly weather data from Meteostat's central data
    repository and aggregate to daily granularity
    """
    # Get all source columns
    source_cols = list(dict.fromkeys([PARAMETER_AGGS[p][0] for p in req.parameters]))

    # Get hourly DataFrame
    ts_hourly = hourly(
        req.station.id,
        req.start,
        req.end,
        parameters=source_cols,
        providers=[Provider.HOURLY],
        timezone=req.station.timezone,
    )

    df_hourly = ts_hourly.fetch(fill=True, sources=True)

    # If no hourly data is available, exit
    if df_hourly is None:
        return None

    # Create daily aggregations
    df = pd.DataFrame()
    for parameter in req.parameters:
        [hourly_param_name, agg_func] = PARAMETER_AGGS[parameter]
        df[parameter] = (
            df_hourly[hourly_param_name]
            .groupby(pd.Grouper(level="time", freq="1D"))
            .agg(agg_func)
        )
        df[f"{parameter}_source"] = (
            df_hourly[f"{hourly_param_name}_source"]
            .groupby(pd.Grouper(level="time", freq="1D"))
            .agg(aggregate_sources)
        )

    # Adjust DataFrame and add index
    df = df.round(1)
    df.index = pd.to_datetime(df.index.astype("datetime64").dt.date)  # type: ignore[union-attr]
    df.index.name = "time"

    # Return reshaped DataFrame
    return reshape_by_source(df)
