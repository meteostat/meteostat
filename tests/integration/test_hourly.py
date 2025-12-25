from datetime import datetime

import meteostat as ms
from meteostat.core.data import data_service
from meteostat.enumerations import Provider, UnitSystem


def test_hourly(mock_hourly_fetch, mock_stations_database):
    """
    It returns a filtered DataFrame
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    df = ts.fetch()

    assert len(df) == 3
    assert df.iloc[0]["temp"] == 8.3


def test_hourly_timezone(mock_hourly_fetch, mock_stations_database):
    """
    It should consider the timezone when filtering the DataFrame
    """
    ts = ms.hourly(
        "10637",
        datetime(2024, 1, 1, 15),
        datetime(2024, 1, 1, 17),
        timezone="Europe/Berlin",
    )
    df = ts.fetch()

    assert len(df) == 3
    assert df.iloc[0]["temp"] == 8.5


def test_hourly_none(mocker, empty_dataframe, mock_stations_database):
    """
    It returns None if provider returns an empty DataFrame
    """
    mocker.patch(
        "meteostat.providers.meteostat.hourly.fetch", return_value=empty_dataframe
    )
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    assert ts.fetch() is None


def test_hourly_count(mock_hourly_fetch, mock_stations_database):
    """
    It counts the non-NaN values for a parameter
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Count for specific parameter
    temp_count = ts.count("temp")
    assert temp_count > 0

    # Count for entire DataFrame
    total_count = ts.count()
    assert total_count >= temp_count


def test_hourly_completeness(mock_hourly_fetch, mock_stations_database):
    """
    It calculates completeness for parameters
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Completeness for specific parameter
    temp_completeness = ts.completeness("temp")
    assert isinstance(temp_completeness, float)
    assert 0 <= temp_completeness <= 1

    # Overall completeness
    overall_completeness = ts.completeness()
    assert isinstance(overall_completeness, float)
    assert 0 <= overall_completeness <= 1


def test_hourly_validate(mock_hourly_fetch, mock_stations_database):
    """
    It validates the time series data
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Validation should return a boolean
    is_valid = ts.validate()
    assert isinstance(is_valid, bool)


def test_hourly_fetch_with_sources(mock_hourly_fetch, mock_stations_database):
    """
    It includes source information in the DataFrame
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    df = ts.fetch(sources=True)

    assert df is not None
    # With sources=True, source columns are added (e.g., temp_source, prcp_source)
    source_cols = [col for col in df.columns if "_source" in col]
    assert len(source_cols) > 0


def test_hourly_fetch_with_fill(mock_hourly_fetch, mock_stations_database):
    """
    It fills missing rows when requested
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    df_filled = ts.fetch(fill=True)
    df_unfilled = ts.fetch(fill=False)

    assert df_filled is not None
    # Filled DataFrame should have at least as many rows as unfilled
    assert len(df_filled) >= len(df_unfilled)


def test_hourly_fetch_with_units(mock_hourly_fetch, mock_stations_database):
    """
    It converts units when requested
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Get data in metric units (default)
    df_metric = ts.fetch(units=UnitSystem.METRIC)
    # Get data in imperial units
    df_imperial = ts.fetch(units=UnitSystem.IMPERIAL)

    assert df_metric is not None
    assert df_imperial is not None

    # Temperature values should differ between unit systems
    if "temp" in df_metric.columns and "temp" in df_imperial.columns:
        metric_temp = df_metric.iloc[0]["temp"]
        imperial_temp = df_imperial.iloc[0]["temp"]
        # Convert: F = C * 9/5 + 32
        expected_imperial = metric_temp * 9 / 5 + 32
        assert abs(imperial_temp - expected_imperial) < 1  # Allow for rounding


def test_hourly_length(mock_hourly_fetch, mock_stations_database):
    """
    It has a length property
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Length should be accessible and greater than 0
    assert len(ts) > 0


def test_hourly_parameters_property(mock_hourly_fetch, mock_stations_database):
    """
    It provides access to available parameters
    """
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))

    # Get parameters
    params = ts.parameters
    assert isinstance(params, list)
    assert len(params) > 0
    assert "temp" in params


def test_hourly_empty_property(
    mock_hourly_fetch, empty_dataframe, mocker, mock_stations_database
):
    """
    It has an empty property that reflects data availability
    """
    # Non-empty case
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    assert ts.empty is False

    # Empty case
    mocker.patch(
        "meteostat.providers.meteostat.hourly.fetch", return_value=empty_dataframe
    )
    ts_empty = ms.hourly("10637", datetime(2024, 1, 1, 0), datetime(2024, 1, 1, 1))
    assert ts_empty.empty is True


def test_hourly_multiple_providers(
    mock_stations_database, mock_dwd_hourly_fetch, mock_dwd_poi_fetch, mock_dwd_mosmix_fetch
):
    ts = ms.hourly(
        "10637",
        datetime(2025, 12, 1, 0, 0),
        datetime(2025, 12, 18, 23, 59),
        providers=[ms.Provider.DWD_HOURLY, ms.Provider.DWD_POI, ms.Provider.DWD_MOSMIX],
    )
    df = ts.fetch(sources=True)
    assert df is not None
    assert len(df) == 432
    assert df.iloc[0]["temp_source"] == Provider.DWD_HOURLY
    assert df.iloc[380]["temp_source"] == Provider.DWD_POI
    assert df.iloc[431]["temp_source"] == Provider.DWD_MOSMIX


def test_hourly_multiple_providers_no_squash(
    mock_stations_database, mock_dwd_hourly_fetch, mock_dwd_poi_fetch, mock_dwd_mosmix_fetch
):
    ts = ms.hourly(
        "10637",
        datetime(2025, 12, 1, 0, 0),
        datetime(2025, 12, 18, 23, 59),
        providers=[ms.Provider.DWD_HOURLY, ms.Provider.DWD_POI, ms.Provider.DWD_MOSMIX],
    )
    df = ts.fetch(sources=True, squash=False)
    df_1 = data_service.filter_time(
        df, datetime(2025, 12, 1, 0, 0), datetime(2025, 12, 1, 0, 59)
    )
    df_2 = data_service.filter_time(
        df, datetime(2025, 12, 16, 16, 0), datetime(2025, 12, 16, 16, 59)
    )
    df_3 = data_service.filter_time(
        df, datetime(2025, 12, 17, 6, 0), datetime(2025, 12, 17, 6, 59)
    )
    df_4 = data_service.filter_time(
        df, datetime(2025, 12, 18, 6, 0), datetime(2025, 12, 18, 6, 59)
    )
    assert df is not None
    assert len(df) == 519
    assert len(df_1) == 1
    assert df_1.index.get_level_values("source").unique().tolist() == [
        Provider.DWD_HOURLY
    ]
    assert len(df_2) == 2
    assert df_2.index.get_level_values("source").unique().tolist() == [
        Provider.DWD_MOSMIX,
        Provider.DWD_POI,
    ]
    assert len(df_3) == 2
    assert df_3.index.get_level_values("source").unique().tolist() == [
        Provider.DWD_MOSMIX,
        Provider.DWD_POI,
    ]
    assert len(df_4) == 1
    assert df_4.index.get_level_values("source").unique().tolist() == [
        Provider.DWD_MOSMIX
    ]
