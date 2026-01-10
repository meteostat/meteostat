"""
Data Service

The Data Service is responsible for fetching meteorological data from
different providers and merging it into a single time series.
"""

from datetime import datetime
from typing import List, Optional, Union, cast

import pandas as pd

from meteostat.api.timeseries import TimeSeries
from meteostat.core.logger import logger
from meteostat.core.parameters import parameter_service
from meteostat.core.providers import provider_service
from meteostat.core.schema import schema_service
from meteostat.enumerations import Parameter, Provider
from meteostat.typing import Station, Request
from meteostat.utils.data import stations_to_df
from meteostat.utils.guards import request_size_guard


class DataService:
    """
    Data Service
    """

    @staticmethod
    def _add_source(df: pd.DataFrame, provider_id: str) -> pd.DataFrame:
        """
        Add source column to DataFrame
        """
        if "source" not in df.index.names:
            df["source"] = provider_id
            df = df.set_index(["source"], append=True)

        return df

    @staticmethod
    def filter_time(
        df: pd.DataFrame,
        start: Union[datetime, None] = None,
        end: Union[datetime, None] = None,
    ) -> pd.DataFrame:
        """
        Filter time series data based on start and end date
        """

        # Return empty DataFrame if input is empty
        if df.empty:
            return df

        # Get time index
        time = df.index.get_level_values("time")

        # Filter & return
        try:
            return df.loc[(time >= start) & (time <= end)] if start and end else df
        except TypeError:
            return (
                df.loc[(time >= start.date()) & (time <= end.date())]
                if start and end
                else df
            )

    @staticmethod
    def concat_fragments(
        fragments: List[pd.DataFrame],
        parameters: List[Parameter],
    ) -> pd.DataFrame:
        """
        Concatenate multiple fragments into a single DataFrame
        """
        try:
            cleaned = [
                df.dropna(how="all", axis=1) if not df.empty else None
                for df in fragments
            ]
            filtered = [df for df in cleaned if df is not None]
            if not filtered:
                return pd.DataFrame()
            df = pd.concat(filtered)
            df = schema_service.fill(df, parameters)
            df = schema_service.purge(df, parameters)
            return df
        except ValueError:
            return pd.DataFrame()

    def _fetch_provider_data(
        self, req: Request, station: Station, provider: Provider
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single weather station and provider
        """
        try:
            # Fetch DataFrame for current provider
            df = provider_service.fetch_data(provider, req, station)

            # Continue if no data was returned
            if df is None:
                return None

            # Add current station ID to DataFrame
            df = pd.concat([df], keys=[station.id], names=["station"])

            # Add source index column to DataFrame
            df = self._add_source(df, provider)

            # Filter DataFrame for requested parameters and time range
            df = self.filter_time(df, req.start, req.end)

            # Drop empty rows
            df = df.dropna(how="all")

            return df

        except Exception:
            logger.error(
                'Could not fetch data for provider "%s"',
                provider,
                exc_info=True,
            )

    def _fetch_station_data(self, req: Request, station: Station) -> List[pd.DataFrame]:
        """
        Fetch data for a single weather station
        """
        fragments = []

        filtered_providers = provider_service.filter_providers(req, station)

        for provider in filtered_providers:
            df = self._fetch_provider_data(req, station, provider)

            # Continue if no data was returned
            if df is None:
                continue

            fragments.append(df)

        return fragments

    def fetch(
        self,
        req: Request,
    ) -> TimeSeries:
        """
        Load meteorological time series data from different providers
        """
        # Guard request
        request_size_guard(req)

        # Convert stations to list if single Station
        stations: List[Station] = (
            cast(List[Station], req.station)
            if isinstance(req.station, list)
            else [req.station]
        )

        logger.debug(
            "%s time series requested for %s station(s)", req.granularity, len(stations)
        )

        # Filter parameters
        req.parameters = parameter_service.filter_parameters(
            req.granularity, req.parameters
        )

        fragments = []

        # Go through all weather stations
        for station in stations:
            station_fragments = self._fetch_station_data(req, station)

            if station_fragments:
                fragments.extend(station_fragments)

        # Merge data in a single DataFrame
        if fragments:
            df = self.concat_fragments(fragments, req.parameters)
        else:
            df = pd.DataFrame()

        # Set data types
        df = schema_service.format(df, req.granularity)

        # Create time series
        ts = TimeSeries(
            req.granularity,
            stations_to_df(stations),
            df,
            req.start,
            req.end,
            req.timezone,
            multi_station=isinstance(req.station, list),
        )

        # Return time series
        return ts


data_service = DataService()
