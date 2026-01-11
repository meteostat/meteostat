from datetime import datetime
import pytest
import meteostat as ms
from meteostat.providers.noaa.ghcnd import fetch
from meteostat.typing import ProviderRequest


@pytest.mark.skip(reason="NOAA GHCND provider tests are taking very long to run.")
def test_noaa_ghcnd():
    """
    It should load data from NOAA GHCND
    """
    ms.config.cache_enable = False

    query = ProviderRequest(
        start=datetime(2021, 2, 1, 15),
        end=datetime(2022, 2, 1, 17),
        station=ms.Station(id="10637", identifiers={"ghcn": "GMW00035032"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    assert len(df) > 1
    assert "temp" in df
    assert "prcp" in df
