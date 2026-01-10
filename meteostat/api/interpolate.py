"""
Interpolation Module

Provides spatial interpolation functions for meteorological data.
"""

from typing import Optional, Union

import numpy as np
import pandas as pd

from meteostat.api.point import Point
from meteostat.api.timeseries import TimeSeries
from meteostat.typing import Station
from meteostat.enumerations import Parameter
from meteostat.interpolation.lapserate import apply_lapse_rate
from meteostat.interpolation.nearest import nearest_neighbor
from meteostat.interpolation.idw import inverse_distance_weighting
from meteostat.utils.data import aggregate_sources, reshape_by_source, stations_to_df
from meteostat.utils.geo import get_distance
from meteostat.utils.parsers import parse_station
from meteostat.core.schema import schema_service
from meteostat.core.logger import logger


# Parameters that are categorical and should not use IDW interpolation
CATEGORICAL_PARAMETERS = {Parameter.WDIR, Parameter.CLDC, Parameter.COCO}


def _create_timeseries(
    ts: TimeSeries, point: Point, df: Optional[pd.DataFrame] = None
) -> TimeSeries:
    """
    Create a TimeSeries object from interpolated DataFrame
    """
    parsed = parse_station(point)
    stations_list = [parsed] if isinstance(parsed, Station) else parsed

    # Convert stations to DataFrame
    stations_df = stations_to_df(stations_list)

    return TimeSeries(
        ts.granularity,
        stations_df,
        df=df,
        start=ts.start,
        end=ts.end,
        timezone=ts.timezone,
    )


def _add_source_columns(
    result: pd.DataFrame,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add source columns to the result DataFrame
    """
    source_cols = [c for c in df.columns if c.endswith("_source")]
    if source_cols:
        grouped = df.groupby("time")[source_cols].agg(aggregate_sources)
        if isinstance(grouped, pd.Series):
            grouped = grouped.to_frame(name=source_cols[0])
        grouped.index.name = "time"

        # Safely align on time and add/fill source columns without causing overlaps
        result_has_time_col = "time" in result.columns
        if result_has_time_col:
            result = result.set_index("time")

        # Ensure both frames align on the same index (time)
        # For each source column, add it if missing or fill NaNs if present
        for col in source_cols:
            if col in grouped.columns:
                if col in result.columns:
                    # Fill missing values in result using aggregated sources
                    result[col] = result[col].where(result[col].notna(), grouped[col])
                else:
                    # Add aggregated source column
                    result[col] = grouped[col]

        if result_has_time_col:
            result = result.reset_index()
    return result


def _prepare_data_with_distances(
    df: pd.DataFrame, point: Point, elevation_weight: float
) -> pd.DataFrame:
    """
    Add distance and elevation calculations to the DataFrame
    """
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

    return df


def _should_use_nearest_neighbor(
    df: pd.DataFrame,
    point: Point,
    distance_threshold: Union[int, None],
    elevation_threshold: Union[int, None],
) -> bool:
    """
    Determine if nearest neighbor should be used based on thresholds
    """
    min_distance = df["distance"].min()
    use_nearest = distance_threshold is None or min_distance <= distance_threshold

    if use_nearest and point.elevation is not None and "elevation" in df.columns:
        min_elev_diff = np.abs(df["elevation"] - point.elevation).min()
        use_nearest = (
            elevation_threshold is None or min_elev_diff <= elevation_threshold
        )

    return use_nearest


def _get_categorical_columns(df: pd.DataFrame) -> list:
    """
    Identify categorical columns in the data (excluding source columns)
    """
    data_cols = [c for c in df.columns if not c.endswith("_source")]
    return [c for c in data_cols if c in CATEGORICAL_PARAMETERS]


def _interpolate_with_nearest_neighbor(
    df: pd.DataFrame,
    ts: TimeSeries,
    point: Point,
    distance_threshold: Union[int, None],
    elevation_threshold: Union[int, None],
) -> Optional[pd.DataFrame]:
    """
    Perform nearest neighbor interpolation with threshold filtering
    """
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
    return nearest_neighbor(df_filtered, ts, point)


def _interpolate_with_idw_and_categorical(
    df: pd.DataFrame,
    ts: TimeSeries,
    point: Point,
    categorical_cols: list,
    power: float,
) -> Optional[pd.DataFrame]:
    """
    Perform IDW interpolation for non-categorical parameters and nearest neighbor for categorical
    """
    # For categorical parameters, always use nearest neighbor
    if categorical_cols:
        df_categorical = nearest_neighbor(df, ts, point)
        # Keep only categorical columns that exist in the result
        existing_categorical = [
            c for c in categorical_cols if c in df_categorical.columns
        ]
        df_categorical = (
            df_categorical[existing_categorical]
            if existing_categorical
            else pd.DataFrame()
        )
    else:
        df_categorical = pd.DataFrame()

    # Perform IDW interpolation for all parameters
    idw_func = inverse_distance_weighting(power=power)
    df_idw = idw_func(df, ts, point)

    # Remove categorical columns from IDW result if they exist
    if not df_categorical.empty and df_idw is not None:
        # Drop categorical columns from IDW result
        idw_cols_to_keep = [c for c in df_idw.columns if c not in categorical_cols]
        df_idw = df_idw[idw_cols_to_keep] if idw_cols_to_keep else pd.DataFrame()

    # Combine categorical (nearest) and non-categorical (IDW) results
    if not df_categorical.empty and not df_idw.empty:
        return pd.concat([df_idw, df_categorical], axis=1)
    elif not df_categorical.empty:
        return df_categorical
    else:
        return df_idw


def _merge_interpolation_results(
    df_nearest: Optional[pd.DataFrame],
    df_idw: Optional[pd.DataFrame],
    use_nearest: bool,
) -> Optional[pd.DataFrame]:
    """
    Merge nearest neighbor and IDW results with appropriate priority
    """
    if use_nearest and df_nearest is not None and len(df_nearest) > 0:
        if df_idw is not None:
            # Combine nearest and IDW results, prioritizing nearest values
            return df_nearest.combine_first(df_idw)
        else:
            return df_nearest
    else:
        return df_idw


def _postprocess_result(
    result: pd.DataFrame, df: pd.DataFrame, ts: TimeSeries
) -> pd.DataFrame:
    """
    Post-process the interpolation result: drop location columns, add sources, format, reshape
    """
    # Drop location-related columns
    result = result.drop(
        [
            "latitude",
            "longitude",
            "elevation",
            "distance",
            "effective_distance",
            "elevation_diff",
        ],
        axis=1,
        errors="ignore",
    )

    # Add source columns
    result = _add_source_columns(result, df)

    # Reshape by source
    result = reshape_by_source(result)

    # Add station index
    result["station"] = "$0001"
    result = result.set_index("station", append=True).reorder_levels(
        ["station", "time", "source"]
    )

    # Reorder columns to match the canonical schema order
    result = schema_service.purge(result, ts.parameters)

    # Format the result using schema_service to apply proper rounding
    result = schema_service.format(result, ts.granularity)

    return result


def interpolate(
    ts: TimeSeries,
    point: Point,
    distance_threshold: Union[int, None] = 5000,
    elevation_threshold: Union[int, None] = 50,
    elevation_weight: float = 10,
    power: float = 2.0,
    lapse_rate: Union[float, None] = 6.5,
    lapse_rate_threshold: int = 50,
) -> TimeSeries:
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
    df = ts.fetch(fill=True, location=True, sources=True)

    # If no data is returned, return None
    if df is None:
        logger.debug("No data available for interpolation. Returning empty TimeSeries.")
        return _create_timeseries(ts, point)

    # Prepare data with distance and elevation calculations
    df = _prepare_data_with_distances(df, point, elevation_weight)

    # Apply lapse rate if specified and elevation is available
    if (
        lapse_rate
        and point.elevation
        and df["elevation_diff"].max() >= lapse_rate_threshold
    ):
        logger.debug("Applying lapse rate correction.")
        df = apply_lapse_rate(df, point.elevation, lapse_rate)

    # Determine if nearest neighbor should be used
    use_nearest = _should_use_nearest_neighbor(
        df, point, distance_threshold, elevation_threshold
    )

    # Identify categorical columns
    categorical_cols = _get_categorical_columns(df)
    logger.debug(f"Categorical columns identified: {categorical_cols}")

    # Perform interpolation
    df_nearest = None
    df_idw = None

    if use_nearest:
        logger.debug("Using nearest neighbor interpolation.")
        df_nearest = _interpolate_with_nearest_neighbor(
            df, ts, point, distance_threshold, elevation_threshold
        )

    # Use IDW if nearest neighbor doesn't provide complete data
    if (
        not use_nearest
        or df_nearest is None
        or len(df_nearest) == 0
        or df_nearest.isna().any().any()
    ):
        logger.debug("Using IDW interpolation.")
        df_idw = _interpolate_with_idw_and_categorical(
            df, ts, point, categorical_cols, power
        )

    # Merge results
    result = _merge_interpolation_results(df_nearest, df_idw, use_nearest)

    # If no data is returned, return None
    if result is None or result.empty:
        return _create_timeseries(ts, point)

    # Post-process result
    result = _postprocess_result(result, df, ts)

    return _create_timeseries(ts, point, result)
