from datetime import datetime
from functools import wraps
from pathlib import Path
import pickle

from meteostat.api.hourly import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_HOURLY
from meteostat.api.daily import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_DAILY
from meteostat.api.monthly import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS_MONTHLY
from meteostat.enumerations import Granularity, Provider
from meteostat.providers.meteostat.hourly import fetch as fetch_hourly
from meteostat.providers.meteostat.daily import fetch as fetch_daily
from meteostat.providers.meteostat.monthly import fetch as fetch_monthly
from meteostat.typing import Request, Station


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
            fixtures_dir = Path(__file__).parent.parent / "fixtures"
            fixtures_dir.mkdir(parents=True, exist_ok=True)
            filepath = fixtures_dir / f"df_{filename}.pickle"
            with open(filepath, "wb") as f:
                pickle.dump(df, f)
            return df

        return wrapper

    return decorator


@fixture("hourly")
def generate_hourly_fixture():
    """
    Generates a fixture DataFrame for hourly data tests
    """
    req = Request(
        granularity=Granularity.HOURLY,
        providers=[Provider.HOURLY],
        parameters=DEFAULT_PARAMETERS_HOURLY,
        station=Station(id="10637"),
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
    req = Request(
        granularity=Granularity.DAILY,
        providers=[Provider.DAILY],
        parameters=DEFAULT_PARAMETERS_DAILY,
        station=Station(id="10637"),
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
    req = Request(
        granularity=Granularity.MONTHLY,
        providers=[Provider.MONTHLY],
        parameters=DEFAULT_PARAMETERS_MONTHLY,
        station=Station(id="10637"),
        start=datetime(2000, 1, 1, 0, 0),
        end=datetime(2020, 12, 31, 23, 59),
    )
    df = fetch_monthly(req)
    return df


generate_hourly_fixture()
generate_daily_fixture()
generate_monthly_fixture()
