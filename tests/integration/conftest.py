"""
Shared fixtures for integration tests
"""

import json
import os

import pandas as pd
import pytest


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
def json_station():
    """Load station fixture data"""
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "fixtures",
        "station_10637.json",
    )
    return json.load(open(fixture_path, "r"))


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
def mock_hourly_fetch(mocker, df_hourly):
    """Mock the hourly fetch function"""
    return mocker.patch(
        "meteostat.providers.meteostat.hourly.fetch", return_value=df_hourly
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
def mock_station(mocker, json_station):
    """Mock the station fetch function"""
    return mocker.patch(
        "meteostat.api.station._fetch_station", return_value=json_station
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
