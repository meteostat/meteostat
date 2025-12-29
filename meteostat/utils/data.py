"""
DataFrame mutations

Meteorological data provided by Meteostat (https://dev.meteostat.net)
under the terms of the Creative Commons Attribution-NonCommercial
4.0 International Public License.

The code is licensed under the MIT license.
"""

from collections import Counter
from datetime import datetime
from itertools import chain
from typing import List

import numpy as np
import pandas as pd

from meteostat.core.providers import provider_service
from meteostat.enumerations import Frequency
from meteostat.typing import Station


def stations_to_df(stations: List[Station]) -> pd.DataFrame:
    """
    Convert list of stations to DataFrame
    """
    assert len(stations) > 0 and all(
        isinstance(station, Station) for station in stations
    )

    return pd.DataFrame.from_records(
        [
            {
                "id": station.id,
                "name": station.name,
                "country": station.country,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "elevation": station.elevation,
                "timezone": station.timezone,
            }
            for station in stations
        ],
        index="id",
    )


def squash_df(df: pd.DataFrame, sources=False) -> pd.DataFrame:
    """
    Squash a DataFrame based on the source priority
    """
    # Capture the columns
    columns = df.columns

    # Add source priority column
    df["source_prio"] = df.index.get_level_values("source").map(
        provider_service.get_source_priority
    )

    # Shift source information to columns
    if sources:
        df = df.reset_index(level="source")
        for column in columns:
            df[f"{column}_source"] = np.where(df[column].notna(), df["source"], np.nan)
        df = df.set_index("source", append=True)

    # Get highest priority value/source for each station and time
    df = (
        df.groupby(level=["station", "time", "source"])
        .last()  # In case of duplicate index, the last row will be prefered
        .sort_values(by="source_prio", ascending=False)
        .groupby(["station", "time"])
        .first()  # Prefer value with highest priority
        .drop("source_prio", axis=1)
    )

    # Order columns and return squashed DataFrame
    return df[order_source_columns(df.columns)] if sources else df


def fill_df(
    df: pd.DataFrame, start: datetime, end: datetime, freq: str
) -> pd.DataFrame:
    """
    Fill a DataFrame with a complete date range for each station
    """
    try:
        iterables = [
            df.index.get_level_values("station").unique(),
            pd.date_range(start=start, end=end, freq=freq),
        ]
        names = ["station", "time"]
        if "source" in df.index.names:
            iterables.append(df.index.get_level_values("source").unique())
            names.append("source")
        # Create a new MultiIndex with every hour for each station
        new_index = pd.MultiIndex.from_product(iterables, names=names)

        # Reindex the DataFrame to add missing rows
        df = df.reindex(index=new_index)
        return df
    except KeyError:
        return df


def localize(df: pd.DataFrame, timezone: str) -> pd.DataFrame:
    """
    Convert time data to any time zone
    """
    return df.tz_localize("UTC", level="time").tz_convert(timezone, level="time")


def reshape_by_source(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape a DataFrame so that the source columns are pivoted into
    their own level of the index
    """
    # Extract value rows and source rows
    value_rows = df.loc[:, ~df.columns.str.endswith("_source")]
    source_rows = df.loc[:, df.columns.str.endswith("_source")]

    # Melt both value_rows and source_rows
    value_melted = value_rows.reset_index().melt(id_vars="time")
    source_melted = source_rows.reset_index().melt(id_vars="time")

    # Remove '_source' from the variable names in source_melted
    source_melted["variable"] = source_melted["variable"].str.replace("_source", "")

    # Merge the melted DataFrames
    merged_df = pd.merge(
        value_melted, source_melted, on=["time", "variable"], suffixes=("", "_source")
    )

    # Drop rows with missing values
    merged_df = merged_df.dropna(subset=["value"])

    # Pivot the DataFrame
    df_pivoted = merged_df.pivot(
        index=["time", "value_source"], columns="variable", values="value"
    )

    # Flatten the MultiIndex
    df_pivoted.index = df_pivoted.index.rename(["time", "source"])
    df_pivoted.columns.name = None

    # Preserve the original parameter column order from value_rows
    # Pivot often produces alphabetical column order; reindex to match input
    ordered_columns = [col for col in value_rows.columns if col in df_pivoted.columns]
    if ordered_columns:
        df_pivoted = df_pivoted.reindex(columns=ordered_columns)

    return df_pivoted


def aggregate_sources(series: pd.Series) -> str:
    """
    Concatenate multiple data sources into a unique source string,
    ordered by the number of occurrences.
    """
    # Extract sources and flatten them
    sources = [str(item) for item in series if pd.notna(item)]
    flat_sources = list(chain(*[source.split() for source in sources]))

    # Count occurrences of each source
    source_counts = Counter(flat_sources)

    # Sort sources by count in descending order
    sorted_sources = sorted(source_counts, key=lambda s: source_counts[s], reverse=True)

    # Concatenate sorted sources into a unique source string
    return " ".join(sorted_sources)


def enforce_freq(df: pd.DataFrame, freq: Frequency) -> pd.DataFrame:
    """
    Enforce a specific frequency on a DataFrame by resampling
    """
    df.index = pd.to_datetime(df.index.get_level_values("time"))
    return df.resample(freq).first()


def order_source_columns(columns: pd.Index) -> List[str]:
    """
    Order source columns
    """
    ordered_columns = []

    for col in columns:
        if not col.endswith("_source"):
            ordered_columns.append(col)
            ordered_columns.append(f"{col}_source")

    return ordered_columns
