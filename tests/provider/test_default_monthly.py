from datetime import datetime
import meteostat as ms
from meteostat.providers.meteostat.monthly import fetch
from meteostat.typing import ProviderRequest


def test_data_monthly():
    """
    Test default monthly data fetching.
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2020, 1, 1),
        end=datetime(2020, 12, 1),
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TMIN, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1, "No data returned for the specified date range."
    assert "tmin" in df, "Minimum temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."
