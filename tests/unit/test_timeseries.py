"""
Test TimeSeries functionality

The code is licensed under the MIT license.
"""

import pytest
import pandas as pd
from datetime import datetime
from meteostat.api.timeseries import TimeSeries
from meteostat.enumerations import Granularity, Parameter


class TestTimeSeriesCompleteness:
    """Test TimeSeries.completeness() method"""

    @pytest.fixture
    def stations_df(self):
        """Create a minimal stations DataFrame for testing."""
        return pd.DataFrame(
            {
                "name": ["Test"],
                "latitude": [50.0],
                "longitude": [8.0],
                "elevation": [100],
            },
            index=pd.Index(["TEST"], name="id"),
        )

    def test_completeness_with_none_start_returns_none(self, stations_df):
        """completeness() should return None when start is None"""
        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        result = ts.completeness()
        assert result is None

    def test_completeness_with_none_end_returns_none(self, stations_df):
        """completeness() should return None when end is None"""
        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=datetime(2024, 1, 1),
            end=None,
        )

        result = ts.completeness()
        assert result is None

    def test_completeness_with_empty_df_and_no_dates(self, stations_df):
        """completeness() on empty DataFrame with no date bounds should return None"""
        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=pd.DataFrame(),
            start=None,
            end=None,
        )

        result = ts.completeness()
        assert result is None

    def test_completeness_with_parameter_and_no_dates(self, stations_df):
        """completeness(parameter) should return None with undefined date range"""
        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        result = ts.completeness(Parameter.TEMP)
        assert result is None

    def test_completeness_target_length_guard(self, stations_df):
        """_target_length should protect against division by zero"""
        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        target_length = ts._target_length
        assert target_length == 0

        result = ts.completeness()
        assert result is None

    def test_completeness_with_valid_dates_and_data(self, stations_df):
        """completeness() should work correctly with valid data and dates"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * 5, dates, ["meteostat"] * 5],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: [20, 21, 22, 23, 24]}, index=index)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 5),
        )

        result = ts.completeness(Parameter.TEMP)
        assert result == 1.0

    def test_completeness_partial_data(self, stations_df):
        """completeness() should calculate correct percentage with partial data"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        values = [20, 21, None, 23, None, None, 26, 27, 28, 29]
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * 10, dates, ["meteostat"] * 10],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: values}, index=index)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        )

        result = ts.completeness(Parameter.TEMP)
        assert result is not None
        assert abs(result - 0.7) < 0.01

    def test_completeness_all_none_values(self, stations_df):
        """completeness() with all None values should return 0.0"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * 5, dates, ["meteostat"] * 5],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: [None] * 5}, index=index)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 5),
        )

        result = ts.completeness(Parameter.TEMP)
        assert result == 0.0


class TestTimeSeriesStartEnd:
    """Test TimeSeries start/end preservation"""

    @pytest.fixture
    def stations_df(self):
        """Create a minimal stations DataFrame for testing."""
        return pd.DataFrame(
            {
                "name": ["Test"],
                "latitude": [50.0],
                "longitude": [8.0],
                "elevation": [100],
            },
            index=pd.Index(["TEST"], name="id"),
        )

    def test_start_end_preserved_with_empty_df(self, stations_df):
        """start/end should be preserved even when df is empty"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=pd.DataFrame(),
            start=start,
            end=end,
        )

        assert ts.start == start
        assert ts.end == end

    def test_start_end_preserved_with_none_df(self, stations_df):
        """start/end should be preserved even when df is None"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=start,
            end=end,
        )

        assert ts.start == start
        assert ts.end == end

    def test_start_end_from_df_when_not_provided(self, stations_df):
        """When not provided, start/end should fall back to df bounds"""
        dates = pd.date_range("2024-01-15", "2024-01-20", freq="D")
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * len(dates), dates, ["meteostat"] * len(dates)],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: range(len(dates))}, index=index)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
        )

        assert ts.start == datetime(2024, 1, 15)
        assert ts.end == datetime(2024, 1, 20)

    def test_explicit_start_end_override_df_bounds(self, stations_df):
        """Explicitly provided start/end should override df bounds"""
        dates = pd.date_range("2024-01-15", "2024-01-20", freq="D")
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * len(dates), dates, ["meteostat"] * len(dates)],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: range(len(dates))}, index=index)

        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
            start=start,
            end=end,
        )

        assert ts.start == start
        assert ts.end == end

    def test_completeness_with_empty_df_and_valid_range(self, stations_df):
        """completeness() should be 0.0 with empty df but valid range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=pd.DataFrame(),
            start=start,
            end=end,
        )

        result = ts.completeness()
        assert result == 0.0

    def test_completeness_per_parameter_with_empty_df(self, stations_df):
        """completeness(parameter) should work with empty df and valid range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=pd.DataFrame(),
            start=start,
            end=end,
        )

        result = ts.completeness(Parameter.TEMP)
        assert result == 0.0

    def test_target_length_with_preserved_dates(self, stations_df):
        """_target_length should work correctly with preserved start/end"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=pd.DataFrame(),
            start=start,
            end=end,
        )

        target = ts._target_length
        assert target == 31

    def test_fetch_fill_needs_start_end(self, stations_df):
        """fetch(fill=True) requires start/end to be set"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 5)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=start,
            end=end,
        )

        result = ts.fetch(fill=True)

        if result is not None:
            assert len(result) >= 5 or result.empty

    def test_no_data_still_tracks_requested_range(self, stations_df):
        """Even with no data found, should remember the requested time range"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=start,
            end=end,
        )

        assert ts.start == start
        assert ts.end == end

        assert ts.completeness() == 0.0

    def test_partial_data_completeness_accurate(self, stations_df):
        """With partial data and explicit date range, completeness should be accurate"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        dates = pd.date_range("2024-01-15", "2024-01-20", freq="D")
        index = pd.MultiIndex.from_arrays(
            [["TEST"] * len(dates), dates, ["meteostat"] * len(dates)],
            names=["station", "time", "source"],
        )
        df = pd.DataFrame({Parameter.TEMP: range(len(dates))}, index=index)

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=df,
            start=start,
            end=end,
        )

        completeness = ts.completeness(Parameter.TEMP)
        expected = 6 / 31
        assert abs(completeness - round(expected, 2)) < 0.01
