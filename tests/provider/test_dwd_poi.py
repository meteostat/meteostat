from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.dwd.poi import fetch
from meteostat.typing import ProviderRequest


def test_dwd_poi():
    """
    It should load data from DWD POI for the last 24 hours
    """
    now = datetime.now()
    query = ProviderRequest(
        start=now - timedelta(hours=24),
        end=now,
        station=ms.Station(id="10637", identifiers={"wmo": "10637"}),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned from DWD POI"
    assert "temp" in df, "Temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."

    # Usually, we would expect exactly 24 hourly entries for the last 24 hours,
    # but due to potential data gaps, we only check for a minimum number of entries.
    assert len(df) > 20, "Insufficient data returned for the last 24 hours."
    assert df["temp"].notna().sum() > 20, "Insufficient temperature data returned."
    assert df["prcp"].notna().sum() > 20, "Insufficient precipitation data returned."
