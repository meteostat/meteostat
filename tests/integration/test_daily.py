from datetime import datetime

import meteostat as ms
from meteostat.enumerations import UnitSystem


def test_daily(mock_daily_fetch, mock_stations_database):
    """
    It returns a filtered DataFrame
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))
    df = ts.fetch()

    assert len(df) == 6
    assert df.iloc[0]["temp"] == 6.6


def test_daily_none(mocker, empty_dataframe, mock_stations_database):
    """
    It returns None if provider returns an empty DataFrame
    """
    mocker.patch(
        "meteostat.providers.meteostat.daily.fetch", return_value=empty_dataframe
    )
    ts = ms.daily("10637", datetime(2024, 1, 1), datetime(2024, 1, 5))
    assert ts.fetch() is None


def test_daily_count(mock_daily_fetch, mock_stations_database):
    """
    It counts the non-NaN values for a parameter
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Count for specific parameter
    temp_count = ts.count("temp")
    assert temp_count > 0

    # Count for entire DataFrame
    total_count = ts.count()
    assert total_count >= temp_count


def test_daily_completeness(mock_daily_fetch, mock_stations_database):
    """
    It calculates completeness for parameters
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Completeness for specific parameter
    temp_completeness = ts.completeness("temp")
    assert isinstance(temp_completeness, float)
    assert 0 <= temp_completeness <= 1

    # Overall completeness
    overall_completeness = ts.completeness()
    assert isinstance(overall_completeness, float)
    assert 0 <= overall_completeness <= 1


def test_daily_validate(mock_daily_fetch, mock_stations_database):
    """
    It validates the time series data
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Validation should return a boolean
    is_valid = ts.validate()
    assert isinstance(is_valid, bool)


def test_daily_fetch_with_sources(mock_daily_fetch, mock_stations_database):
    """
    It includes source information in the DataFrame
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))
    df = ts.fetch(sources=True)

    assert df is not None
    # With sources=True, source columns are added (e.g., temp_source, prcp_source)
    source_cols = [col for col in df.columns if "_source" in col]
    assert len(source_cols) > 0


def test_daily_fetch_with_fill(mock_daily_fetch, mock_stations_database):
    """
    It fills missing rows when requested
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))
    df_filled = ts.fetch(fill=True)
    df_unfilled = ts.fetch(fill=False)

    assert df_filled is not None
    # Filled DataFrame should have at least as many rows as unfilled
    assert len(df_filled) >= len(df_unfilled)


def test_daily_fetch_with_units(mock_daily_fetch, mock_stations_database):
    """
    It converts units when requested
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Get data in metric units (default)
    df_metric = ts.fetch(units=UnitSystem.METRIC)
    # Get data in imperial units
    df_imperial = ts.fetch(units=UnitSystem.IMPERIAL)

    assert df_metric is not None
    assert df_imperial is not None

    # Temperature values should differ between unit systems
    # Metric: Celsius, Imperial: Fahrenheit
    if "temp" in df_metric.columns and "temp" in df_imperial.columns:
        # Imperial temperatures should be higher for positive Celsius values
        metric_temp = df_metric.iloc[0]["temp"]
        imperial_temp = df_imperial.iloc[0]["temp"]
        # Convert: F = C * 9/5 + 32
        expected_imperial = metric_temp * 9 / 5 + 32
        assert abs(imperial_temp - expected_imperial) < 1  # Allow for rounding


def test_daily_length(mock_daily_fetch, mock_stations_database):
    """
    It has a length property
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Length should be accessible and greater than 0
    assert len(ts) > 0


def test_daily_parameters_property(mock_daily_fetch, mock_stations_database):
    """
    It provides access to available parameters
    """
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))

    # Get parameters
    params = ts.parameters
    assert isinstance(params, list)
    assert len(params) > 0
    assert "temp" in params


def test_daily_empty_property(
    mock_daily_fetch, empty_dataframe, mocker, mock_stations_database
):
    """
    It has an empty property that reflects data availability
    """
    # Non-empty case
    ts = ms.daily("10637", datetime(2024, 1, 5), datetime(2024, 1, 10))
    assert ts.empty is False

    # Empty case
    mocker.patch(
        "meteostat.providers.meteostat.daily.fetch", return_value=empty_dataframe
    )
    ts_empty = ms.daily("10637", datetime(2024, 1, 1), datetime(2024, 1, 5))
    assert ts_empty.empty is True
