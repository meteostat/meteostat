from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.dwd.mosmix import fetch
from meteostat.typing import ProviderRequest


def test_dwd_mosmix_forecast():
    """
    Test that the DWD MOSMIX provider returns data for the day seven days from now.
    """
    # Calculate the date seven days from now
    target_date = datetime.now() + timedelta(days=7)
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    end = datetime(target_date.year, target_date.month, target_date.day, 23, 59)

    query = ProviderRequest(
        start=start,
        end=end,
        station=ms.Station(id="10637", identifiers={"mosmix": "10637"}),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned from DWD MOSMIX"
    assert "temp" in df, "Temperature data is missing altogether."

    # The provider will return all forecast data, regardless of the requested date range.
    # Therefore, we are just testing if there is a reasonable amount of non-missing data.
    assert df["temp"].notna().sum() > 20, (
        "Insufficient temperature data returned for the 7th day."
    )

    # Check if at least one datetime on the 7th day is present in the index.
    # Here we're making sure the time series contains data for a date multiple days ahead.
    # This is important, so we can detect provider issues early.
    time_index = df.index.get_level_values("time")
    has_target_date = any(t.date() == target_date.date() for t in time_index)
    assert has_target_date, f"No data found for the 7th day ({target_date.date()})"
