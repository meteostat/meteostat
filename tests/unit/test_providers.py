"""
Test ProviderService.fetch_data()

The code is licensed under the MIT license.
"""

from datetime import date

import pandas as pd

from meteostat.core.providers import ProviderService
from meteostat.enumerations import Granularity, Grade, Parameter, Priority
from meteostat.typing import ProviderSpec, Request, Station


def _make_station() -> Station:
    return Station(id="10637")


def _make_request(provider_id: str) -> Request:
    return Request(
        granularity=Granularity.HOURLY,
        providers=[provider_id],
        parameters=[Parameter.TEMP],
        station=_make_station(),
    )


class TestFetchData:
    """Test fetch_data() guards against providers with no fetch module"""

    def test_returns_none_for_unknown_provider(self):
        service = ProviderService(providers=[])

        df = service.fetch_data("unknown", _make_request("unknown"), _make_station())

        assert df is None

    def test_returns_none_for_provider_without_module(self):
        provider = ProviderSpec(
            id="reanalysis",
            name="Metadata-only provider",
            granularity=Granularity.HOURLY,
            priority=Priority.LOWEST,
            grade=Grade.ANALYSIS,
            license=None,
            parameters=[Parameter.TEMP],
            start=date(1950, 1, 1),
        )
        service = ProviderService(providers=[provider])

        df = service.fetch_data(
            "reanalysis", _make_request("reanalysis"), _make_station()
        )

        assert df is None

    def test_dispatches_to_module_when_present(self, monkeypatch):
        provider = ProviderSpec(
            id="dummy",
            name="Dummy provider",
            granularity=Granularity.HOURLY,
            priority=Priority.LOWEST,
            grade=Grade.ANALYSIS,
            license=None,
            parameters=[Parameter.TEMP],
            start=date(1950, 1, 1),
            module="tests.unit.fixtures.dummy_provider",
        )
        service = ProviderService(providers=[provider])

        df = service.fetch_data("dummy", _make_request("dummy"), _make_station())

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
