"""
Shared fixtures for integration tests
"""

import os
from datetime import date

import pandas as pd
import pytest

from meteostat.core.providers import provider_service
from meteostat.enumerations import Provider
from meteostat.typing import ProviderRequest


@pytest.fixture
def df_daily():
    """Load daily fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_daily.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_hourly():
    """Load hourly fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_hourly.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_hourly_second_station():
    """Load hourly fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_hourly_10635.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_hourly_third_station():
    """Load hourly fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_hourly_10532.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_monthly():
    """Load monthly fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_monthly.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_dwd_hourly():
    """Load hourly fixture data from DWD provider"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_dwd_hourly.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_dwd_poi():
    """Load hourly POI fixture data from DWD provider"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_dwd_poi.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def df_dwd_mosmix():
    """Load hourly MOSMIX fixture data from DWD provider"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "df_dwd_mosmix.pickle",
    )
    return pd.read_pickle(fixture_path)


@pytest.fixture
def str_stations_database_file_path():
    """Return the stations.db fixture path"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "stations.db",
    )
    return fixture_path


@pytest.fixture
def mock_daily_fetch(mocker, df_daily):
    """Mock the daily fetch function"""
    return mocker.patch(
        "meteostat.providers.meteostat.daily.fetch", return_value=df_daily
    )


@pytest.fixture
def mock_hourly_fetch(
    mocker, df_hourly, df_hourly_second_station, df_hourly_third_station
):
    """Mock the hourly fetch function with station-specific data"""

    def side_effect(req: ProviderRequest):
        # Return different DataFrames based on station ID
        if req.station.id == "10635":
            return df_hourly_second_station
        elif req.station.id == "10532":
            return df_hourly_third_station
        else:
            return df_hourly

    return mocker.patch(
        "meteostat.providers.meteostat.hourly.fetch", side_effect=side_effect
    )


@pytest.fixture
def mock_monthly_fetch(mocker, df_monthly):
    """Mock the monthly fetch function"""
    return mocker.patch(
        "meteostat.providers.meteostat.monthly.fetch", return_value=df_monthly
    )


@pytest.fixture
def mock_dwd_hourly_fetch(mocker, df_dwd_hourly):
    """Mock the DWD hourly fetch function"""
    return mocker.patch(
        "meteostat.providers.dwd.hourly.fetch", return_value=df_dwd_hourly
    )


@pytest.fixture
def mock_dwd_poi_fetch(mocker, df_dwd_poi):
    """Mock the DWD POI fetch function"""
    return mocker.patch("meteostat.providers.dwd.poi.fetch", return_value=df_dwd_poi)


@pytest.fixture
def mock_dwd_mosmix_fetch(mocker, df_dwd_mosmix):
    """Mock the DWD MOSMIX fetch function"""
    return mocker.patch(
        "meteostat.providers.dwd.mosmix.fetch", return_value=df_dwd_mosmix
    )


@pytest.fixture
def mock_stations_database(mocker, str_stations_database_file_path):
    """Mock the stations database _get_file_path function"""
    return mocker.patch(
        "meteostat.api.stations.stations._get_file_path",
        return_value=str_stations_database_file_path,
    )


@pytest.fixture
def empty_dataframe():
    """Return an empty DataFrame for testing None cases"""
    return pd.DataFrame()


@pytest.fixture(autouse=True)
def patch_provider_start_date(mocker):
    """Patch the MOSMIX provider's start date to allow test data to be picked up"""
    # Patch the provider_service.get_provider method
    original_get_provider = provider_service.get_provider

    def patched_get_provider(provider_id):
        if provider_id in (
            Provider.DWD_MOSMIX,
            Provider.DWD_POI,
        ):
            # Get the original provider using the unpatched method
            original_provider = original_get_provider(provider_id)

            if original_provider:
                # Create a modified provider spec with an earlier start date
                modified_provider = original_provider.__class__(
                    id=original_provider.id,
                    name=original_provider.name,
                    granularity=original_provider.granularity,
                    priority=original_provider.priority,
                    grade=original_provider.grade,
                    license=original_provider.license,
                    requires=original_provider.requires,
                    parameters=original_provider.parameters,
                    start=date(2025, 1, 1),  # Set to an earlier date to allow test data
                    end=original_provider.end,
                    countries=original_provider.countries,
                    module=original_provider.module,
                )
                return modified_provider

            raise ValueError(f"Provider {provider_id} not found")

        return original_get_provider(provider_id)

    mocker.patch.object(
        provider_service, "get_provider", side_effect=patched_get_provider
    )
