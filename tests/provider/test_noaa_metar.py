import os
from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.noaa.metar import fetch
from meteostat.typing import ProviderRequest


def test_noaa_metar():
    """
    It should load data from NOAA METAR for the last 24 hours
    """
    ms.config.aviationweather_user_agent = os.environ.get("METEOSTAT_USER_AGENT")

    now = datetime.now()
    start = now - timedelta(hours=24)

    query = ProviderRequest(
        start=start,
        end=now,
        station=ms.Station(id="10637", identifiers={"icao": "EDDF"}),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned from NOAA METAR"
    assert "temp" in df, "Temperature data is missing altogether."

    # Usually, we would expect at least 24 entries for the last 24 hours,
    # but due to potential data gaps, we only check for a minimum number of entries.
    assert len(df) > 20, "Insufficient data returned for the last 24 hours."
    assert df["temp"].notna().sum() > 20, "Insufficient temperature data returned."
