from datetime import datetime
from meteostat.api.hourly import DEFAULT_PARAMETERS
from meteostat.enumerations import Granularity, Provider
from meteostat.providers.meteostat.hourly import fetch
from meteostat.typing import Request, Station

def generate_hourly_fixture():
    """
    Generates a fixture DataFrame for hourly data tests
    """
    req = Request(
        granularity=Granularity.HOURLY,
        providers=[Provider.HOURLY],
        parameters=[DEFAULT_PARAMETERS],
        station=Station(id="10637"),
        start=datetime(2024, 1, 1, 0, 0),
        end=datetime(2024, 12, 31, 23, 59),
    )
    df = fetch(req)
    return df

print(generate_hourly_fixture())