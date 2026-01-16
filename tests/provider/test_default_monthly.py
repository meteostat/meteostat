from datetime import datetime
from dateutil.relativedelta import relativedelta
import meteostat as ms
from meteostat.providers.meteostat.monthly import fetch
from meteostat.typing import ProviderRequest


def test_data_monthly():
    """
    Test default monthly data fetching.
    """
    ms.config.cache_enable = False

    end = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start = end - relativedelta(months=12)

    query = ProviderRequest(
        start=start,
        end=end,
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TMIN, ms.Parameter.PRCP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "tmin" in df, "Minimum temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."
    assert "source" in df.index.names, "Source data is missing altogether."

    # The provider will return all data, regardless of the requested date range.
    # Therefore, we are just testing if there is a reasonable amount of non-missing data.
    assert df["tmin"].notna().sum() >= 8, (
        "Insufficient minimum temperature data returned."
    )
    assert df["prcp"].notna().sum() >= 8, "Insufficient precipitation data returned."

    # Check if six months ago is present in the index
    six_months_ago = end - relativedelta(months=6)
    assert six_months_ago in df.index.get_level_values("time"), (
        f"Date six months ago ({six_months_ago}) is not in the index"
    )
