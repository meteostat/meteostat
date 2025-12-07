"""
TimeSeries Class

A class to handle meteorological time series data.
"""

from copy import copy
from datetime import datetime
from itertools import chain
from math import floor
from statistics import mean
from typing import List, Optional

import pandas as pd

from meteostat.core.parameters import parameter_service
from meteostat.core.providers import provider_service
from meteostat.core.schema import schema_service
from meteostat.enumerations import Parameter, Granularity, Provider
from meteostat.typing import License
from meteostat.utils.data import fill_df, localize, squash_df


class TimeSeries:
    """
    TimeSeries class which provides features which are
    used across all granularities
    """

    granularity: Granularity
    stations: Optional[pd.DataFrame] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    timezone: Optional[str] = None

    _df: Optional[pd.DataFrame] = None
    _multi_station: bool = False

    def __init__(
        self,
        granularity: Granularity,
        stations: Optional[pd.DataFrame],
        df: Optional[pd.DataFrame],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timezone: Optional[str] = None,
        multi_station: bool = False,
    ) -> None:
        self.granularity = granularity
        self.stations = stations
        self.timezone = timezone
        self._multi_station = multi_station
        if df is not None and not df.empty:
            self._df = df
            self.start = start if start else df.index.get_level_values("time").min()
            self.end = end if end else df.index.get_level_values("time").max()

    def __len__(self) -> int:
        """
        Return number of rows in DataFrame
        """
        return len(self._df) if self._df is not None else 0

    def __str__(self) -> str:
        """
        Return a stringified version of the DataFrame
        """
        return self._df.__str__() if self._df is not None else "Empty time series"

    @property
    def _target_length(self) -> int:
        """
        Expected number of non-NaN values
        """
        if not self.start or not self.end:
            return 0

        diff = self.end - self.start

        return (
            diff.days + 1
            if self.granularity is Granularity.DAILY
            else floor(diff.total_seconds() / 3600) + 1
        ) * len(self.stations)

    @property
    def parameters(self) -> List[Parameter]:
        """
        Get parameters
        """
        return self._df.columns.to_list() if self._df is not None else []

    @property
    def freq(self) -> Optional[str]:
        """
        The time series frequency.

        Returns a Pandas offset alias string (e.g. "1h", "1D", "1M") or
        `None` for granularities where a regular frequency does not apply
        (e.g. normals).
        """
        if self.granularity is Granularity.HOURLY:
            return "1h"

        if self.granularity is Granularity.DAILY:
            return "1D"

        if self.granularity is Granularity.MONTHLY:
            return "1M"

        # Normals (climatological normals) do not have a regular time
        # frequency in the same sense as timeseries data.
        if self.granularity is Granularity.NORMALS:
            return None

        return None

    @property
    def empty(self) -> bool:
        """
        Is the time series empty?
        """
        return True if self._df is None else self._df.empty
    
    @property
    def providers(self) -> List[Provider]:
        """
        Get included providers
        """
        providers: List[str] = self._df.index.get_level_values("source").unique().to_list()
        return list(set(chain.from_iterable([provider.split(' ') for provider in providers])))

    @property
    def licenses(self) -> List[License]:
        """
        Get licenses
        """
        providers = [
            provider_service.get_provider(provider_id)
            for provider_id in self.providers
        ]

        return [provider.license for provider in providers if provider.license is not None]
    
    @property
    def attribution(self) -> str:
        """
        Attribution string
        """
        attributions = [
            "Meteostat",
            *set([
                license.attribution
                for license in self.licenses
                if license.attribution
            ]),
        ]

        return ", ".join(attributions)

    @property
    def commercial(self) -> bool:
        """
        Is commercial use allowed?
        """
        return all(license.commercial for license in self.licenses)

    def validate(self) -> bool:
        """
        Does the time series pass all validations?
        """
        df = self.fetch(fill=True, clean=False)

        for col in df:
            parameter = parameter_service.get_parameter(col, self.granularity)

            for validator in parameter.validators:
                test = validator(df[col])

                if not test.all():
                    return False

        return True

    # TODO: Investigate if still required
    def filter_stations(self, station: str | List[str], exclude=False) -> "TimeSeries":
        """
        Filter data by weather station(s)
        """
        temp = copy(self)
        mask = self._df.index.get_level_values("station").isin(
            station if isinstance(station, list) else [station]
        )
        temp._df = temp._df[mask if not exclude else ~mask]
        return temp

    # TODO: Investigate if still required
    def filter_providers(
        self, provider: Provider | List[Provider], exclude=False
    ) -> "TimeSeries":
        """
        Filter data by provider(s)
        """
        temp = copy(self)
        mask = self._df.index.get_level_values("source").isin(
            provider if isinstance(provider, list) else [provider]
        )
        temp._df = temp._df[mask if not exclude else ~mask]
        return temp

    def fetch(
        self,
        squash=True,
        fill=False,
        sources=False,
        location=False,
        clean=True,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch the time series data as a DataFrame.

        Parameters
        ----------
        squash : bool, optional
            Whether to squash the DataFrame by source. Defaults to True.
        fill : bool, optional
            Whether to fill missing rows in the DataFrame. Defaults to False.
        sources : bool, optional
            Whether to include source information in the DataFrame. Defaults to False.
        location : bool, optional
            Whether to include location information (latitude, longitude, elevation)
            in the DataFrame. Defaults to False.
        clean : bool, optional
            Whether to clean the DataFrame according to the schema. Defaults to True.

        Returns
        -------
        pd.DataFrame or None
            The time series data as a DataFrame, or None if no data is available.
        """
        df = copy(self._df)

        if df is None:
            return None

        if squash:
            df = squash_df(df, sources=sources)

        if clean:
            df = schema_service.clean(df, self.granularity)

        if fill:
            df = fill_df(df, self.start, self.end, self.freq)

        if self.timezone:
            df = localize(df, self.timezone)

        if location:
            df = df.join(
                self.stations[["latitude", "longitude", "elevation"]], on="station"
            )

        # Remove station index level if not a multi-station query
        if not self._multi_station and "station" in df.index.names:
            df = df.droplevel("station")

        return df.sort_index()

    def count(self, parameter: Optional[Parameter | str] = None) -> int:
        """
        Get number of non-NaN values for a specific parameter.
        If no parameter is specified, it returns the count for the entire DataFrame.

        Parameters
        ----------
        parameter : Parameter or str
            The parameter to count non-NaN values for. If None, counts for the entire DataFrame.

        Returns
        -------
        int
            The count of non-NaN values for the specified parameter or the entire DataFrame.
        """
        if self._df is None:
            return 0
        
        if parameter is None:
            return self._df.count().max()
        
        return self._df[
            parameter if isinstance(parameter, Parameter) else parameter
        ].count()

    def completeness(self, parameter: Optional[Parameter | str] = None) -> float:
        """
        Get completeness for a specific parameter or the entire DataFrame.

        Parameters
        ----------
        parameter : Parameter or str, optional
            The parameter to calculate completeness for.
            If None, calculates for the entire DataFrame.

        Returns
        -------
        float
            The completeness ratio for the specified parameter or the entire DataFrame.
            Returns 0 if no data is available, 1 if complete, or a value between 0 and 1 otherwise.
        """
        df = self.fetch()

        if df is None:
            return 0

        if parameter:
            return round(
                self.count(parameter) / self._target_length,
                2,
            )

        return round(mean([self.completeness(p) for p in df.columns]), 2)
