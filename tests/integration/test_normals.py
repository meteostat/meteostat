import meteostat as ms
from meteostat.enumerations import UnitSystem


def test_normals(mock_monthly_fetch, mock_station):
    """
    It returns a filtered DataFrame
    """
    ts = ms.normals("10637", 2005, 2015)
    df = ts.fetch()

    assert len(df) == 12
    assert df.iloc[0]["temp"] == 2.3


def test_normals_none(mocker, empty_dataframe, mock_station):
    """
    It returns None if provider returns an empty DataFrame
    """
    mocker.patch("meteostat.providers.meteostat.monthly.fetch", return_value=empty_dataframe)
    ts = ms.normals("10637", 2005, 2015)
    assert ts.fetch() is None


def test_normals_count(mock_monthly_fetch, mock_station):
    """
    It counts the non-NaN values for a parameter
    """
    ts = ms.normals("10637", 2005, 2015)
    
    # Count for specific parameter
    temp_count = ts.count("temp")
    assert temp_count > 0
    
    # Count for entire DataFrame
    total_count = ts.count()
    assert total_count >= temp_count


def test_normals_completeness(mock_monthly_fetch, mock_station):
    """
    It calculates completeness for parameters
    """
    ts = ms.normals("10637", 2005, 2015)
    
    # Completeness for specific parameter
    temp_completeness = ts.completeness("temp")
    assert isinstance(temp_completeness, float)
    assert 0 <= temp_completeness <= 1
    
    # Overall completeness
    overall_completeness = ts.completeness()
    assert isinstance(overall_completeness, float)
    assert 0 <= overall_completeness <= 1


def test_normals_validate(mock_monthly_fetch, mock_station):
    """
    It validates the time series data
    """
    ts = ms.normals("10637", 2005, 2015)
    
    # Validation should return a boolean
    is_valid = ts.validate()
    assert isinstance(is_valid, bool)


def test_normals_fetch_with_sources(mock_monthly_fetch, mock_station):
    """
    It includes source information in the DataFrame
    """
    ts = ms.normals("10637", 2005, 2015)
    df = ts.fetch(sources=True)
    
    assert df is not None
    # With sources=True, source columns are added (e.g., temp_source, prcp_source)
    source_cols = [col for col in df.columns if "_source" in col]
    assert len(source_cols) > 0


def test_normals_fetch_with_units(mock_monthly_fetch, mock_station):
    """
    It converts units when requested
    """
    ts = ms.normals("10637", 2005, 2015)
    
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
        expected_imperial = metric_temp * 9/5 + 32
        assert abs(imperial_temp - expected_imperial) < 1  # Allow for rounding


def test_normals_length(mock_monthly_fetch, mock_station):
    """
    It has a length property
    """
    ts = ms.normals("10637", 2005, 2015)
    
    # Length should be accessible and greater than 0
    assert len(ts) > 0


def test_normals_parameters_property(mock_monthly_fetch, mock_station):
    """
    It provides access to available parameters
    """
    ts = ms.normals("10637", 2005, 2015)
    
    # Get parameters
    params = ts.parameters
    assert isinstance(params, list)
    assert len(params) > 0
    assert "temp" in params


def test_normals_empty_property(mock_monthly_fetch, empty_dataframe, mocker, mock_station):
    """
    It has an empty property that reflects data availability
    """
    # Non-empty case
    ts = ms.normals("10637", 2005, 2015)
    assert ts.empty is False
    
    # Empty case
    mocker.patch("meteostat.providers.meteostat.monthly.fetch", return_value=empty_dataframe)
    ts_empty = ms.normals("10637", 2005, 2015)
    assert ts_empty.empty is True
