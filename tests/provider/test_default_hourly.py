from datetime import datetime, timedelta
import meteostat as ms
from meteostat.providers.meteostat.hourly import fetch
from meteostat.typing import ProviderRequest


def test_data_hourly():
    """
    Test that the default hourly provider returns data from three days in the past
    to seven days in the future.
    """
    # Calculate the date range: 3 days ago to 7 days from now
    now = datetime.now()
    start_date = now - timedelta(days=3)
    end_date = now + timedelta(days=7)
    start = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
    end = datetime(end_date.year, end_date.month, end_date.day, 23, 59)

    query = ProviderRequest(
        start=start,
        end=end,
        station=ms.Station(id="10637"),
        parameters=[ms.Parameter.TEMP],
    )
    df = fetch(query)

    # Check if data is returned at all.
    assert df is not None and not df.empty, "No data returned at all."
    assert "temp" in df, "Temperature data is missing altogether."
    assert "source" in df.index.names, "Source data is missing altogether."

    # The provider will return all data, regardless of the requested date range.
    # Therefore, we are just testing if there is a reasonable amount of non-missing data.
    assert df["temp"].notna().sum() > 200, "Insufficient temperature data returned."

    # Check if data from both the past and future is present in the index
    time_index = df.index.get_level_values("time")
    has_past_date = any(t.date() == start_date.date() for t in time_index)
    has_future_date = any(t.date() == end_date.date() for t in time_index)
    assert has_past_date, f"No data found for the start date ({start_date.date()})"
    assert has_future_date, f"No data found for the end date ({end_date.date()})"

    # Check that the start date has at least one source that is no model data
    start_date_mask = [t.date() == start_date.date() for t in time_index]
    start_date_df = df.iloc[start_date_mask]
    source_index = start_date_df.index.get_level_values("source")
    has_non_mosmix_source = any(s != ms.Provider.DWD_MOSMIX for s in source_index)
    assert has_non_mosmix_source, (
        f"No non-model source found for the start date ({start_date.date()})"
    )

    # Check that all data on the end date has DWD_MOSMIX as its source
    end_date_mask = [t.date() == end_date.date() for t in time_index]
    end_date_df = df.iloc[end_date_mask]
    end_date_sources = end_date_df.index.get_level_values("source")
    all_mosmix_source = all(s == ms.Provider.DWD_MOSMIX for s in end_date_sources)
    assert all_mosmix_source, (
        f"Not all data on the end date ({end_date.date()}) has model data as its source"
    )
