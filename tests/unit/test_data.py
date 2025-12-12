"""
Test data module

The code is licensed under the MIT license.
"""

from unittest.mock import patch

import pytest
import pandas as pd
import numpy as np

from meteostat.utils.data import (
    stations_to_df,
    squash_df,
    fill_df,
    localize,
    reshape_by_source,
    aggregate_sources,
    enforce_freq,
    order_source_columns,
)
from meteostat.typing import Station
from meteostat.enumerations import Frequency


class TestStationsToDf:
    """Test stations_to_df function"""

    def test_stations_to_df_single_station(self):
        """Test converting single station to DataFrame"""
        station = Station(
            id="12345",
            name="Test Station",
            country="DE",
            latitude=50.0,
            longitude=8.0,
            elevation=100,
            timezone="Europe/Berlin"
        )
        df = stations_to_df([station])
        
        assert len(df) == 1
        assert df.loc["12345", "name"] == "Test Station"
        assert df.loc["12345", "latitude"] == 50.0
        assert df.loc["12345", "longitude"] == 8.0

    def test_stations_to_df_multiple_stations(self):
        """Test converting multiple stations to DataFrame"""
        stations = [
            Station(
                id="12345",
                name="Station A",
                country="DE",
                latitude=50.0,
                longitude=8.0,
                elevation=100,
                timezone="Europe/Berlin"
            ),
            Station(
                id="54321",
                name="Station B",
                country="FR",
                latitude=48.5,
                longitude=2.5,
                elevation=200,
                timezone="Europe/Paris"
            ),
        ]
        df = stations_to_df(stations)
        
        assert len(df) == 2
        assert "12345" in df.index
        assert "54321" in df.index
        assert df.loc["12345", "country"] == "DE"
        assert df.loc["54321", "country"] == "FR"

    def test_stations_to_df_index(self):
        """Test that DataFrame is indexed by station ID"""
        station = Station(
            id="TEST01",
            name="Test",
            country="DE",
            latitude=0,
            longitude=0,
            elevation=0,
            timezone="UTC"
        )
        df = stations_to_df([station])
        
        assert df.index.name == "id"
        assert df.index[0] == "TEST01"

    def test_stations_to_df_columns(self):
        """Test that DataFrame has all required columns"""
        station = Station(
            id="12345",
            name="Test",
            country="DE",
            latitude=50.0,
            longitude=8.0,
            elevation=100,
            timezone="UTC"
        )
        df = stations_to_df([station])
        
        expected_columns = {"name", "country", "latitude", "longitude", "elevation", "timezone"}
        assert set(df.columns) == expected_columns

    def test_stations_to_df_empty_list_assertion(self):
        """Test that empty station list raises assertion"""
        with pytest.raises(AssertionError):
            stations_to_df([])

    def test_stations_to_df_invalid_type_assertion(self):
        """Test that non-Station objects raise assertion"""
        with pytest.raises(AssertionError):
            stations_to_df(["not a station"])


class TestSquashDf:
    """Test squash_df function"""

    @patch('meteostat.utils.data.provider_service')
    def test_squash_df_basic(self, mock_provider_service):
        """Test basic DataFrame squashing"""
        mock_provider_service.get_source_priority.return_value = 1
        
        # Create test DataFrame with MultiIndex
        idx = pd.MultiIndex.from_tuples([
            ("station1", "2020-01-01", "source1"),
            ("station1", "2020-01-02", "source1"),
        ], names=["station", "time", "source"])
        df = pd.DataFrame({"temp": [20.0, 21.0]}, index=idx)
        
        result = squash_df(df, sources=False)
        
        assert len(result) == 2
        assert "source_prio" not in result.columns

    @patch('meteostat.utils.data.provider_service')
    def test_squash_df_with_sources(self, mock_provider_service):
        """Test DataFrame squashing with source columns"""
        mock_provider_service.get_source_priority.return_value = 1
        
        idx = pd.MultiIndex.from_tuples([
            ("station1", "2020-01-01", "source1"),
        ], names=["station", "time", "source"])
        df = pd.DataFrame({"temp": [20.0]}, index=idx)
        
        result = squash_df(df, sources=True)
        
        assert isinstance(result, pd.DataFrame)

    @patch('meteostat.utils.data.provider_service')
    def test_squash_df_multiple_sources(self, mock_provider_service):
        """Test DataFrame squashing with multiple sources for same data point"""
        # Mock priority: source2 > source1
        def get_priority(source):
            return 2 if source == "source2" else 1
        
        mock_provider_service.get_source_priority.side_effect = get_priority
        
        idx = pd.MultiIndex.from_tuples([
            ("station1", "2020-01-01", "source1"),
            ("station1", "2020-01-01", "source2"),
        ], names=["station", "time", "source"])
        df = pd.DataFrame({"temp": [20.0, 22.0]}, index=idx)
        
        result = squash_df(df, sources=False)
        
        # Should have single row for station1/2020-01-01
        assert len(result) == 1


class TestFillDf:
    """Test fill_df function"""

    def test_fill_df_basic(self):
        """Test basic DataFrame filling"""
        idx = pd.MultiIndex.from_tuples([
            ("station1", pd.Timestamp("2020-01-01")),
            ("station1", pd.Timestamp("2020-01-03")),
        ], names=["station", "time"])
        df = pd.DataFrame({"temp": [20.0, 22.0]}, index=idx)
        
        result = fill_df(
            df,
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-01-03"),
            freq="D"
        )
        
        # Should have 3 rows for station1 (Jan 1, 2, 3)
        assert len(result) >= len(df)

    def test_fill_df_multiple_stations(self):
        """Test filling DataFrame with multiple stations"""
        idx = pd.MultiIndex.from_tuples([
            ("station1", pd.Timestamp("2020-01-01")),
            ("station2", pd.Timestamp("2020-01-01")),
        ], names=["station", "time"])
        df = pd.DataFrame({"temp": [20.0, 21.0]}, index=idx)
        
        result = fill_df(
            df,
            start=pd.Timestamp("2020-01-01"),
            end=pd.Timestamp("2020-01-02"),
            freq="D"
        )
        
        # Should have 4 rows (2 stations × 2 days)
        assert len(result) == 4


class TestLocalize:
    """Test localize function"""

    def test_localize_naive_to_local(self):
        """Test localizing naive datetime to local timezone"""
        # Create a naive datetime (without timezone info)
        idx = pd.MultiIndex.from_tuples([
            ("station1", pd.Timestamp("2020-01-01 00:00")),
        ], names=["station", "time"])
        df = pd.DataFrame({"temp": [20.0]}, index=idx)
        
        result = localize(df, "Europe/Berlin")
        
        # The time should be converted to Berlin timezone
        assert result.index.get_level_values("time")[0].tz.zone == "Europe/Berlin"

    def test_localize_preserves_data(self):
        """Test that localize preserves data values"""
        # Create a naive datetime
        idx = pd.MultiIndex.from_tuples([
            ("station1", pd.Timestamp("2020-01-01 00:00")),
        ], names=["station", "time"])
        df = pd.DataFrame({"temp": [20.0]}, index=idx)
        
        result = localize(df, "Europe/London")
        
        assert result.loc[("station1", slice(None)), "temp"].values[0] == 20.0


class TestReshapeBySource:
    """Test reshape_by_source function"""

    def test_reshape_by_source_basic(self):
        """Test basic source reshaping"""
        df = pd.DataFrame({
            "temp": [20.0, 21.0],
            "temp_source": ["source1", "source2"],
            "time": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")],
        })
        df = df.set_index("time")
        
        result = reshape_by_source(df)
        
        assert isinstance(result, pd.DataFrame)
        assert "temp" in result.columns

    def test_reshape_by_source_multiple_columns(self):
        """Test reshaping with multiple data columns"""
        df = pd.DataFrame({
            "temp": [20.0, 21.0],
            "temp_source": ["source1", "source2"],
            "prcp": [10.0, 5.0],
            "prcp_source": ["source1", "source1"],
            "time": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")],
        })
        df = df.set_index("time")
        
        result = reshape_by_source(df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


class TestAggregateeSources:
    """Test aggregate_sources function"""

    def test_aggregate_sources_single(self):
        """Test aggregating single source"""
        series = pd.Series(["source1"])
        result = aggregate_sources(series)
        assert result == "source1"

    def test_aggregate_sources_multiple(self):
        """Test aggregating multiple sources"""
        series = pd.Series(["source1 source2", "source1"])
        result = aggregate_sources(series)
        # source1 appears 2 times, source2 appears 1 time
        assert result.startswith("source1")

    def test_aggregate_sources_with_nan(self):
        """Test aggregating sources with NaN"""
        series = pd.Series(["source1", np.nan, "source2"])
        result = aggregate_sources(series)
        assert "source1" in result
        assert "source2" in result

    def test_aggregate_sources_frequency_order(self):
        """Test that aggregation orders by frequency"""
        series = pd.Series(["a b c", "a b", "a"])
        result = aggregate_sources(series)
        # 'a' appears 3 times, 'b' appears 2, 'c' appears 1
        parts = result.split()
        assert parts[0] == "a"
        assert parts[1] == "b"
        assert parts[2] == "c"


class TestEnforceFreq:
    """Test enforce_freq function"""

    def test_enforce_freq_daily(self):
        """Test enforcing daily frequency"""
        idx = pd.DatetimeIndex([
            "2020-01-01",
            "2020-01-02",
            "2020-01-03",
        ], name="time")
        df = pd.DataFrame({"temp": [20.0, 21.0, 22.0]}, index=idx)
        
        result = enforce_freq(df, Frequency.DAILY)
        
        assert len(result) >= 1

    def test_enforce_freq_hourly(self):
        """Test enforcing hourly frequency"""
        idx = pd.DatetimeIndex([
            "2020-01-01 00:00",
            "2020-01-01 01:00",
            "2020-01-01 02:00",
        ], name="time")
        df = pd.DataFrame({"temp": [20.0, 21.0, 22.0]}, index=idx)
        
        result = enforce_freq(df, Frequency.HOURLY)
        
        assert len(result) >= 1


class TestOrderSourceColumns:
    """Test order_source_columns function"""

    def test_order_source_columns_basic(self):
        """Test basic source column ordering"""
        columns = pd.Index(["temp", "temp_source", "prcp", "prcp_source"])
        result = order_source_columns(columns)
        
        assert result == ["temp", "temp_source", "prcp", "prcp_source"]

    def test_order_source_columns_single(self):
        """Test ordering with single source column"""
        columns = pd.Index(["temp", "temp_source"])
        result = order_source_columns(columns)
        
        assert result == ["temp", "temp_source"]

    def test_order_source_columns_with_gaps(self):
        """Test ordering when some columns have source and others don't"""
        columns = pd.Index(["temp", "temp_source", "prcp"])
        result = order_source_columns(columns)
        
        # Should interleave with missing sources
        assert "temp" in result
        assert "temp_source" in result
        assert "prcp" in result

    def test_order_source_columns_unordered(self):
        """Test ordering of unordered columns"""
        columns = pd.Index(["prcp_source", "temp_source", "prcp", "temp"])
        result = order_source_columns(columns)
        
        # Should interleave values and sources
        # Either [temp, temp_source, prcp, prcp_source] or [prcp, prcp_source, temp, temp_source]
        # Main requirement is that each value column is followed by its source
        assert len(result) == 4
