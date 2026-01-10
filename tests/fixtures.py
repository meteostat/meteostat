from datetime import datetime
from functools import wraps
from pathlib import Path
import pickle

from meteostat.api.hourly import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_HOURLY
from meteostat.api.daily import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_DAILY
from meteostat.api.monthly import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_MONTHLY
from meteostat.api.stations import stations
from meteostat.api.config import config
from meteostat.core.data import data_service
from meteostat.providers.meteostat.hourly import fetch as fetch_hourly
from meteostat.providers.meteostat.daily import fetch as fetch_daily
from meteostat.providers.meteostat.monthly import fetch as fetch_monthly
from meteostat.providers.dwd.hourly import fetch as fetch_dwd_hourly
from meteostat.providers.dwd.poi import fetch as fetch_dwd_poi
from meteostat.providers.dwd.mosmix import fetch as fetch_dwd_mosmix
from meteostat.typing import ProviderRequest, Station


FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Ensure the fixtures directory exists
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def fixture(filename):
    """
    Decorator that persists the returned DataFrame as a pickle file.

    Args:
        filename: Name of the file (without extension) to save under tests/fixtures/{filename}.pickle
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            df = func(*args, **kwargs)
            filepath = FIXTURES_DIR / f"df_{filename}.pickle"
            with open(filepath, "wb") as f:
                pickle.dump(df, f)
            return df

        return wrapper

    return decorator


def generate_stations_db_fixture():
    """
    Generates a fixture JSON file for stations database
    """
    config.stations_db_file = str(FIXTURES_DIR / "stations.db")

    stations._get_file_path()


@fixture("hourly")
def generate_hourly_fixture():
    """
    Generates a fixture DataFrame for hourly data tests
    """
    req = ProviderRequest(
        station=Station(id="10637"),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=datetime(2024, 1, 1, 0, 0),
        end=datetime(2024, 12, 31, 23, 59),
    )
    df = fetch_hourly(req)
    return df


@fixture("hourly_10635")
def generate_hourly_fixture_second_station():
    """
    Generates a fixture DataFrame for hourly data tests
    """
    req = ProviderRequest(
        station=Station(id="10635"),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=datetime(2024, 1, 1, 0, 0),
        end=datetime(2024, 12, 31, 23, 59),
    )
    df = fetch_hourly(req)
    return df


@fixture("hourly_10532")
def generate_hourly_fixture_third_station():
    """
    Generates a fixture DataFrame for hourly data tests
    """
    req = ProviderRequest(
        station=Station(id="10532"),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=datetime(2024, 1, 1, 0, 0),
        end=datetime(2024, 12, 31, 23, 59),
    )
    df = fetch_hourly(req)
    return df


@fixture("daily")
def generate_daily_fixture():
    """
    Generates a fixture DataFrame for daily data tests
    """
    req = ProviderRequest(
        station=Station(id="10637"),
        parameters=DEFAULT_PARAMETERS_DAILY,
        start=datetime(2024, 1, 1, 0, 0),
        end=datetime(2024, 12, 31, 23, 59),
    )
    df = fetch_daily(req)
    return df


@fixture("monthly")
def generate_monthly_fixture():
    """
    Generates a fixture DataFrame for monthly data tests
    """
    req = ProviderRequest(
        station=Station(id="10637"),
        parameters=DEFAULT_PARAMETERS_MONTHLY,
        start=datetime(2000, 1, 1, 0, 0),
        end=datetime(2020, 12, 31, 23, 59),
    )
    df = fetch_monthly(req)
    return df


@fixture("dwd_hourly")
def generate_dwd_hourly_fixture():
    """
    Generates a fixture DataFrame for DWD HOURLY data tests
    """
    start = datetime(2025, 12, 1, 0, 0)
    end = datetime(2025, 12, 17, 23, 59)
    req = ProviderRequest(
        station=Station(id="10637", identifiers={"national": "01420"}),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=start,
        end=end,
    )
    df = fetch_dwd_hourly(req)
    df = data_service.filter_time(df, start, end)
    return df


@fixture("dwd_poi")
def generate_dwd_poi_fixture():
    """
    Generates a fixture DataFrame for DWD POI data tests
    """
    req = ProviderRequest(
        station=Station(id="10637", identifiers={"wmo": "10637"}),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=datetime(2025, 12, 1, 0, 0),
        end=datetime(2025, 12, 23, 23, 59),
    )
    df = fetch_dwd_poi(req)
    return df


@fixture("dwd_mosmix")
def generate_dwd_mosmix_fixture():
    """
    Generates a fixture DataFrame for DWD MOSMIX data tests
    """
    req = ProviderRequest(
        station=Station(id="10637", identifiers={"mosmix": "10637"}),
        parameters=DEFAULT_PARAMETERS_HOURLY,
        start=datetime(2025, 12, 1, 0, 0),
        end=datetime(2025, 12, 15, 23, 59),
    )
    df = fetch_dwd_mosmix(req)
    return df


generate_stations_db_fixture()
generate_hourly_fixture()
generate_hourly_fixture_second_station()
generate_hourly_fixture_third_station()
generate_daily_fixture()
generate_monthly_fixture()
generate_dwd_hourly_fixture()
generate_dwd_poi_fixture()
generate_dwd_mosmix_fixture()
