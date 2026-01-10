from itertools import combinations
from statistics import mean

import numpy as np
import pandas as pd

from meteostat.api.timeseries import TimeSeries
from meteostat.api.config import config
from meteostat.enumerations import Parameter


def lapse_rate(ts: TimeSeries, parameter: Parameter = Parameter.TEMP) -> float | None:
    """
    Calculate the lapse rate (temperature gradient) in degrees Celsius per kilometer
    based on temperature and elevation data from multiple stations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing temperature and elevation data for multiple stations.

    Returns
    -------
    float
        Calculated lapse rate in degrees Celsius per kilometer.
    """
    df = ts.fetch(location=True)

    if df is None or "elevation" not in df.columns or parameter not in df.columns:
        return None

    elev_by_station = df["elevation"].groupby(level="station").first()
    temp_by_station = df[parameter].groupby(level="station").mean()

    if len(elev_by_station) < 2 or len(temp_by_station) < 2:
        return None

    lapse_rates = []

    for a, b in combinations(elev_by_station.index, 2):
        if (
            pd.isna(elev_by_station[a])
            or pd.isna(elev_by_station[b])
            or pd.isna(temp_by_station[a])
            or pd.isna(temp_by_station[b])
            or elev_by_station[a] == elev_by_station[b]
        ):
            continue

        temp_diff = temp_by_station[a] - temp_by_station[b]
        elev_diff = elev_by_station[a] - elev_by_station[b]

        # multiply by -1 to get positive lapse rate for decreasing temp
        # with increasing elevation
        lapse_rate = (temp_diff / elev_diff) * 1000 * -1
        lapse_rates.append(lapse_rate)

    if not lapse_rates:
        return None

    return mean(lapse_rates)


def apply_lapse_rate(
    df: pd.DataFrame, elevation: int, lapse_rate: float
) -> pd.DataFrame:
    """
    Calculate approximate temperature at target elevation
    using a given lapse rate.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data to be adjusted.
    elevation : int
        Target elevation in meters.
    lapse_rate : float
        Lapse rate (temperature gradient) in degrees Celsius per kilometer.

    Returns
    -------
    pd.DataFrame
        DataFrame with adjusted temperature values.
    """
    for col in config.lapse_rate_parameters:
        if col in df.columns:
            df.loc[df[col] != np.nan, col] = round(
                df[col] + ((lapse_rate / 1000) * (df["elevation"] - elevation)), 1
            )

    return df
