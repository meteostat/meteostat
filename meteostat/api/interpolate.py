"""
Interpolation Module

Provides spatial interpolation functions for meteorological data.
"""

from typing import Optional, Union

import numpy as np
import pandas as pd

from meteostat.api.point import Point
from meteostat.api.timeseries import TimeSeries
from meteostat.interpolation.lapserate import apply_lapse_rate
from meteostat.interpolation.nearest import nearest_neighbor
from meteostat.interpolation.idw import inverse_distance_weighting
from meteostat.utils.geo import get_distance


# TODO: Make interpolate return TimeSeries instead of DataFrame
def interpolate(
    ts: TimeSeries,
    point: Point,
    distance_threshold: Union[int, None] = 5000,
    elevation_threshold: Union[int, None] = 50,
    elevation_weight: float = 10,
    power: float = 2.0,
    lapse_rate: Union[float, None] = 6.5,
    lapse_rate_threshold: int = 50,
) -> Optional[pd.DataFrame]:
    """
    Interpolate time series data spatially to a specific point.

    Parameters
    ----------
    ts : TimeSeries
        The time series to interpolate.
    point : Point
        The point to interpolate the data for.
    distance_threshold : int, optional
        Maximum distance (in meters) to use nearest neighbor (default: 5000).
        Beyond this, IDW is used.
    elevation_threshold : int, optional
        Maximum elevation difference (in meters) to use nearest neighbor (default: 50).
        Beyond this, IDW is used even if distance is within threshold.
    elevation_weight : float, optional
        Weight for elevation difference in distance calculation (default: 0.1).
        The effective distance is calculated as:
        sqrt(horizontal_distance^2 + (elevation_diff * elevation_weight)^2)
    power : float, optional
        Power parameter for IDW (default: 2.0). Higher values give more
        weight to closer stations.
    lapse_rate : float, optional
        Apply lapse rate correction based on elevation difference (default: 6.5).
    lapse_rate_threshold : int, optional
        Elevation difference threshold (in meters) to apply lapse rate correction
        (default: 50). If the elevation difference between the point and stations
        is less than this, no correction is applied.

    Returns
    -------
    pd.DataFrame or None
        A DataFrame containing the interpolated data for the specified point,
        or None if no data is available.
    """
    # Fetch DataFrame, filling missing values and adding location data
    df = ts.fetch(fill=True, location=True)

    # If no data is returned, return None
    if df is None:
        return None

    # Add distance column
    df["distance"] = get_distance(
        point.latitude, point.longitude, df["latitude"], df["longitude"]
    )

    # Add effective distance column if elevation is available
    if point.elevation is not None and "elevation" in df.columns:
        elev_diff = np.abs(df["elevation"] - point.elevation)
        df["effective_distance"] = np.sqrt(
            df["distance"] ** 2 + (elev_diff * elevation_weight) ** 2
        )
    else:
        df["effective_distance"] = df["distance"]

    # Add elevation difference column
    if "elevation" in df.columns and point.elevation is not None:
        df["elevation_diff"] = np.abs(df["elevation"] - point.elevation)
    else:
        df["elevation_diff"] = np.nan

    # Apply lapse rate if specified and elevation is available
    if (
        lapse_rate
        and point.elevation
        and df["elevation_diff"].max() >= lapse_rate_threshold
    ):
        df = apply_lapse_rate(df, point.elevation, lapse_rate)

    # Check if any stations are close enough for nearest neighbor
    min_distance = df["distance"].min()
    use_nearest = distance_threshold is None or min_distance <= distance_threshold
    if use_nearest and point.elevation is not None and "elevation" in df.columns:
        # Calculate minimum elevation difference
        min_elev_diff = np.abs(df["elevation"] - point.elevation).min()
        use_nearest = (
            elevation_threshold is None or min_elev_diff <= elevation_threshold
        )

    # Initialize variables
    df_nearest = None
    df_idw = None

    # Perform nearest neighbor if applicable
    if use_nearest:
        # Filter applicable stations based on thresholds
        distance_filter = (
            pd.Series([True] * len(df), index=df.index)
            if distance_threshold is None
            else (df["distance"] <= distance_threshold)
        )
        elevation_filter = (
            pd.Series([True] * len(df), index=df.index)
            if elevation_threshold is None
            else (np.abs(df["elevation"] - point.elevation) <= elevation_threshold)
        )
        df_filtered = df[distance_filter & elevation_filter]
        df_nearest = nearest_neighbor(df_filtered, ts, point)

    # Check if we need to use IDW
    if (
        not use_nearest
        or df_nearest is None
        or len(df_nearest) == 0
        or df_nearest.isna().any().any()
    ):
        # Perform IDW interpolation
        idw_func = inverse_distance_weighting(power=power)
        df_idw = idw_func(df, ts, point)

    # Merge DataFrames with priority to nearest neighbor
    if use_nearest and df_nearest is not None and len(df_nearest) > 0:
        if df_idw is not None:
            # Combine nearest and IDW results, prioritizing nearest values
            result = df_nearest.combine_first(df_idw)
        else:
            result = df_nearest
    else:
        result = df_idw

    # If no data is returned, return None
    if result is None or result.empty:
        return None

    # Drop location-related columns & return
    return result.drop(
        [
            "latitude",
            "longitude",
            "elevation",
            "distance",
            "effective_distance",
            "elevation_diff",
        ],
        axis=1,
    )
