"""
Climate Normals

Access climate normals data for one or multiple weather stations.
"""

from typing import List, Optional

import numpy as np
import pandas as pd

from meteostat.enumerations import Parameter, Provider, Granularity
from meteostat.core.schema import schema_service
from meteostat.api.monthly import DEFAULT_PARAMETERS, monthly
from meteostat.api.timeseries import TimeSeries
from meteostat.typing import Station
from meteostat.api.point import Point
from meteostat.utils.data import reshape_by_source
from meteostat.utils.parsers import parse_year


def normals(
    station: str | Station | Point | List[str | Station | Point] | pd.DataFrame,
    start: int = 1961,
    end: int = 1990,
    parameters: Optional[List[Parameter]] = None,
    providers: Optional[List[Provider]] = None,
    max_missing: int = 3,
):
    """
    Access climate normals data.

    Parameters
    ----------
    station : str, Station, Point, List[str | Station | Point], pd.Index, pd.Series
        Weather station(s) or Point(s) to query data for. Can be a single station/point or a list.
        Points are converted to virtual stations with IDs like $0001, $0002, etc.
    start : int, optional
        Start year for the data query. Defaults to 1961.
    end : int, optional
        End year for the data query. Defaults to 1990.
    parameters : List[Parameter], optional
        List of parameters to include in the data query. Defaults to a set of common parameters.
    providers : List[Provider], optional
        List of data providers to use for the query. Defaults to the monthly provider.
    max_missing : int, optional
        Maximum number of missing values allowed in a month to calculate the mean. Defaults to 3.

    Returns
    -------
    TimeSeries
        A TimeSeries object containing the climate normals data for the specified
        stations and parameters.
    """
    if parameters is None:
        parameters = DEFAULT_PARAMETERS
    if providers is None:
        providers = [Provider.MONTHLY]

    def _mean(group: pd.Series):
        """
        Calculate the monthly mean from multiple years of monthly data
        """
        if group.isna().sum() > max_missing:
            return np.nan
        return group.mean()

    # Fetch monthly data for the specified stations and parameters
    ts = monthly(
        station,
        parse_year(start),
        parse_year(end, True),
        parameters=parameters,
        providers=providers,
    )
    df = ts.fetch(sources=True)

    # Process data if available
    if df is not None and not df.empty:
        # Add station level if only a single station is provided
        if not ts._multi_station:
            df = pd.concat(
                [df],
                keys=[ts.stations.index.get_level_values("id")[0]],
                names=["station"],
            )

        # Extract month from time index
        df["month"] = df.index.get_level_values("time").month

        # Create aggregation functions for different column types
        agg_funcs = {}
        for col in df.columns:
            if col.endswith("_source"):
                # For source columns, concatenate unique values
                agg_funcs[col] = lambda x: ", ".join(x.dropna().unique())
            elif col == "txmx":
                # For temperature maximum, use max function
                agg_funcs[col] = lambda x: x.max() if not x.isna().all() else np.nan
            elif col == "txmn":
                # For temperature minimum, use min function
                agg_funcs[col] = lambda x: x.min() if not x.isna().all() else np.nan
            else:
                # For data columns, use the mean function
                agg_funcs[col] = _mean

        # Apply aggregation functions
        df = df.groupby(["station", "month"]).agg(agg_funcs)
        df = df.rename_axis(index={"month": "time"})

        # Separate parameter columns from source columns for formatting
        param_cols = [str(param) for param in parameters if str(param) in df.columns]
        source_cols = [col for col in df.columns if col.endswith("_source")]

        # Format only the parameter columns
        if param_cols:
            df_data = schema_service.format(df[param_cols], Granularity.NORMALS)
            # Combine formatted parameter columns with unformatted source columns
            if source_cols:
                df = pd.concat([df_data, df[source_cols]], axis=1)
            else:
                df = df_data

        # Reshape data by source for each station
        df_fragments = []
        for s in df.index.get_level_values("station").unique():
            station_df = df.loc[s]
            fragment = reshape_by_source(station_df)
            fragment = pd.concat([fragment], keys=[s], names=["station"])
            df_fragments.append(fragment)

        df = pd.concat(df_fragments)
    else:
        df = None

    # Return the final TimeSeries object
    return TimeSeries(
        granularity=Granularity.NORMALS,
        stations=ts.stations,
        df=df,
        start=ts.start,
        end=ts.end,
        multi_station=ts._multi_station,
    )
