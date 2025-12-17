"""
Provider Service

The Provider Service provides methods to interact with data providers.
"""

from datetime import datetime
from importlib import import_module
from statistics import fmean
from typing import List, Optional, TypeGuard, cast

import pandas as pd

from meteostat.core.logger import logger
from meteostat.enumerations import Granularity, Priority, Provider
from meteostat.providers.index import DEFAULT_PROVIDERS
from meteostat.typing import (
    ProviderRequest,
    ProviderSpec,
    Station,
    Request,
)


class ProviderService:
    """
    Provider Service
    """

    _providers: List[ProviderSpec]

    def __init__(self, providers: List[ProviderSpec]) -> None:
        self._providers = providers

    @property
    def providers(self) -> List[ProviderSpec]:
        """
        Get supported providers
        """
        return self._providers

    def register(self, provider: ProviderSpec) -> None:
        """
        Register a provider
        """
        self._providers.append(provider)

    def get_provider(self, provider_id: Provider | str) -> Optional[ProviderSpec]:
        """
        Get provider by ID
        """
        return next(
            (provider for provider in self._providers if provider.id == provider_id),
            None,
        )

    def _get_provider_priority(self, provider_id: Provider | str) -> int:
        """
        Get priority of a provider by its ID
        """
        baselines = {
            Granularity.HOURLY: 0,
            Granularity.DAILY: 100,
            Granularity.MONTHLY: 200,
            Granularity.NORMALS: 300,
        }

        provider = self.get_provider(provider_id)

        if not provider:
            return Priority.NONE

        baseline = baselines[provider.granularity]

        return int(provider.priority + baseline)

    def get_source_priority(self, source: str) -> float:
        """
        Get priority of a source string
        """
        provider_ids = source.split(" ")

        if len(provider_ids) == 1:
            return self._get_provider_priority(provider_ids[0])

        priorities = [
            self._get_provider_priority(provider) for provider in provider_ids
        ]

        return fmean(priorities)

    def filter_providers(self, query: Request, station: Station) -> List[Provider]:
        """
        Get a filtered list of providers
        """

        def _filter(provider_id: Provider) -> TypeGuard[Provider]:
            provider = self.get_provider(provider_id)

            if provider is None:
                return False

            # Filter out providers with diverging granularities
            if provider.granularity is not query.granularity:
                logger.error(
                    "Provider '%s' does not support granularity '%s'",
                    provider_id,
                    query.granularity,
                )
                return False

            # Filter out providers with no overlap in parameters
            if set(provider.parameters).isdisjoint(query.parameters):
                logger.info(
                    "Provider '%s' does not support any requested parameter",
                    provider_id,
                )
                return False

            # Filter out providers which do not serve the station's country
            if provider.countries and station.country not in provider.countries:
                logger.info(
                    "Skipping provider '%s' as it does not serve the station's country ('%s')",
                    provider_id,
                    station.country,
                )
                return False

            # Filter out providers which stopped providing data before the request's start date
            if query.end and query.end < datetime.combine(
                provider.start, datetime.min.time()
            ):
                logger.info(
                    "Skipping provider '%s' as it stopped providing data before request start",
                    provider_id,
                )
                return False

            # Filter out providers which only started providing data after the request's end date
            if (
                provider.end is not None
                and query.start is not None
                and query.start > datetime.combine(provider.end, datetime.max.time())
            ):
                logger.info(
                    "Skipping provider '%s' as it only started providing data after request end",
                    provider_id,
                )
                return False

            return True

        return list(filter(_filter, query.providers))

    def fetch_data(
        self, provider_id: Provider, req: Request, station: Station
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from a given provider
        """
        provider = self.get_provider(provider_id)

        if not provider:
            return None

        query = ProviderRequest(
            station=station,
            start=req.start
            or (
                datetime.combine(provider.start, datetime.min.time())
                if provider.start
                else None
            ),
            end=req.end or (provider.end or datetime.now()),
            parameters=req.parameters,
        )

        module = import_module(cast(str, provider.module))
        df = module.fetch(query)

        return df


provider_service = ProviderService(providers=DEFAULT_PROVIDERS)
