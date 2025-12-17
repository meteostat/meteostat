"""
Inverse Distance Weighting (IDW) Interpolation

Implements IDW interpolation for spatial weather data with support for
elevation-weighted distance calculations.
"""

from typing import Callable

import numpy as np
import pandas as pd

from meteostat.api.point import Point
from meteostat.api.timeseries import TimeSeries


def inverse_distance_weighting(
    power: float = 2.0,
) -> Callable:
    """
    Interpolate values using Inverse Distance Weighting (IDW).

    This method calculates interpolated values as a weighted average of nearby
    stations, where weights decrease with distance. Optionally incorporates
    elevation differences in the distance calculation.

    Parameters
    ----------
    power : float, optional
        Power parameter for IDW (default: 2.0). Higher values give more
        weight to closer stations.
    elevation_weight : float, optional
        Weight for elevation difference in distance calculation (default: 0.1).
        The effective distance is calculated as:
        sqrt(horizontal_distance^2 + (elevation_diff * elevation_weight)^2)

    Notes
    -----
    - If elevation data is missing for either the point or stations, only
    horizontal distance is used.
    - Stations with zero effective distance get weight of 1.0, all others get 0.
    - All numeric columns except location-related ones are interpolated.
    """

    def _get_df(
        df: pd.DataFrame,
        ts: TimeSeries,
        point: Point,
    ) -> pd.DataFrame:
        # Group by time to interpolate each timestamp separately
        grouped = df.groupby(pd.Grouper(level="time", freq=ts.freq))

        # List to store interpolated results for each time period
        interpolated_results = []

        for time_idx, group in grouped:
            if group.empty:
                continue

            effective_distance = group["effective_distance"]

            # Calculate weights using IDW formula: w = 1 / d^p
            # Handle zero distance case (station at exact location)
            min_distance = effective_distance.min()
            if min_distance == 0:
                # If any station is at the exact location, use only that station
                weights = (effective_distance == 0).astype(float)
            else:
                # Standard IDW weights
                weights = 1.0 / (effective_distance**power)

            # Normalize weights so they sum to 1
            weights = weights / weights.sum()

            # Get numeric columns to interpolate (exclude location-related columns)
            location_cols = ["latitude", "longitude", "elevation", "distance"]
            numeric_cols = [
                col
                for col in group.columns
                if col not in location_cols
                and pd.api.types.is_numeric_dtype(group[col])
            ]

            # Calculate weighted average for each numeric column
            interpolated_row = {}
            for col in numeric_cols:
                # Only use non-NaN values for interpolation
                valid_mask = group[col].notna()
                if valid_mask.any():
                    valid_values = group.loc[valid_mask, col]
                    valid_weights = weights[valid_mask]
                    # Re-normalize weights for valid values only
                    valid_weights = valid_weights / valid_weights.sum()
                    interpolated_row[col] = (valid_values * valid_weights).sum()
                else:
                    # If all values are NaN, result is NaN
                    interpolated_row[col] = np.nan

            # Add location information from the point
            interpolated_row["latitude"] = point.latitude
            interpolated_row["longitude"] = point.longitude
            if point.elevation is not None:
                interpolated_row["elevation"] = point.elevation
            interpolated_row["distance"] = 0  # Distance from point to itself

            # Create a DataFrame row with the time index
            result_df = pd.DataFrame(
                [interpolated_row], index=pd.DatetimeIndex([time_idx])
            )
            result_df.index.name = "time"
            interpolated_results.append(result_df)

        # Combine all time periods
        if interpolated_results:
            result = pd.concat(interpolated_results)
            return result
        else:
            return pd.DataFrame()

    return _get_df
