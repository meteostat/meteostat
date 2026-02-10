"""
Test IDW (Inverse Distance Weighting) interpolation

The code is licensed under the MIT license.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock

from meteostat.interpolation.idw import inverse_distance_weighting
from meteostat.api.point import Point
from meteostat.api.timeseries import TimeSeries


class TestIDW:
    """Test IDW interpolation handles edge cases correctly"""

    def _create_mock_timeseries(self, freq: str = "h") -> TimeSeries:
        """Create a mock TimeSeries object."""
        ts = MagicMock(spec=TimeSeries)
        ts.freq = freq
        return ts

    def test_zero_weight_sum_returns_nan_not_zero(self):
        """When all weights sum to zero, IDW should handle it gracefully"""
        time = datetime(2024, 1, 1, 12, 0)
        df = pd.DataFrame(
            {
                "effective_distance": [1e308, 1e308],
                "temp": [20.0, 25.0],
                "latitude": [50.0, 51.0],
                "longitude": [8.0, 9.0],
                "elevation": [100, 200],
                "distance": [1000, 2000],
            },
            index=pd.MultiIndex.from_tuples(
                [(time, "A"), (time, "B")], names=["time", "station"]
            ),
        )

        point = Point(50.5, 8.5, 150)
        ts = self._create_mock_timeseries()

        idw_func = inverse_distance_weighting(power=2.0)
        result = idw_func(df, ts, point)

        if result.empty:
            pass
        elif "temp" in result.columns:
            temp_val = result["temp"].iloc[0]
            assert np.isnan(temp_val) or (19 < temp_val < 26)

    def test_valid_weights_sum_zero_returns_nan_not_zero(self):
        """When valid weights for a column sum to zero, result should be NaN, not 0"""
        time = datetime(2024, 1, 1, 12, 0)

        df = pd.DataFrame(
            {
                "effective_distance": [0.001, 1e308],
                "temp": [np.nan, 25.0],
                "latitude": [50.0, 51.0],
                "longitude": [8.0, 9.0],
                "elevation": [100, 200],
                "distance": [1, 1000000],
            },
            index=pd.MultiIndex.from_tuples(
                [(time, "A"), (time, "B")], names=["time", "station"]
            ),
        )

        point = Point(50.0, 8.0, 100)
        ts = self._create_mock_timeseries()

        idw_func = inverse_distance_weighting(power=2.0)
        result = idw_func(df, ts, point)

        assert not result.empty and "temp" in result.columns

        temp_val = result["temp"].iloc[0]

        assert np.isnan(temp_val) or abs(temp_val - 25.0) < 1.0

    def test_underflow_weights_returns_nan_not_zero(self):
        """When weights underflow to zero, result should be NaN or skip, not 0"""
        time = datetime(2024, 1, 1, 12, 0)

        df = pd.DataFrame(
            {
                "effective_distance": [1e160, 1e160, 1e160],
                "temp": [20.0, 22.0, 24.0],
                "latitude": [50.0, 51.0, 52.0],
                "longitude": [8.0, 9.0, 10.0],
                "elevation": [100, 200, 300],
                "distance": [1e10, 1e10, 1e10],
            },
            index=pd.MultiIndex.from_tuples(
                [(time, "A"), (time, "B"), (time, "C")], names=["time", "station"]
            ),
        )

        point = Point(50.5, 8.5, 150)
        ts = self._create_mock_timeseries()

        idw_func = inverse_distance_weighting(power=2.0)
        result = idw_func(df, ts, point)

        if not result.empty and "temp" in result.columns:
            temp_val = result["temp"].iloc[0]

            assert np.isnan(temp_val) or (19 < temp_val < 25)

    def test_normal_case_still_works(self):
        """Normal distances should produce valid interpolation"""
        time = datetime(2024, 1, 1, 12, 0)

        df = pd.DataFrame(
            {
                "effective_distance": [10.0, 20.0, 30.0],
                "temp": [20.0, 22.0, 24.0],
                "latitude": [50.0, 50.1, 50.2],
                "longitude": [8.0, 8.1, 8.2],
                "elevation": [100, 110, 120],
                "distance": [10, 20, 30],
            },
            index=pd.MultiIndex.from_tuples(
                [(time, "A"), (time, "B"), (time, "C")], names=["time", "station"]
            ),
        )

        point = Point(50.05, 8.05, 105)
        ts = self._create_mock_timeseries()

        idw_func = inverse_distance_weighting(power=2.0)
        result = idw_func(df, ts, point)

        assert not result.empty
        assert "temp" in result.columns

        temp_val = result["temp"].iloc[0]
        assert np.isfinite(temp_val)
        assert 19 < temp_val < 25

    def test_all_nan_column_returns_nan(self):
        """When all stations have NaN for a column, result should be NaN"""
        time = datetime(2024, 1, 1, 12, 0)

        df = pd.DataFrame(
            {
                "effective_distance": [10.0, 20.0],
                "temp": [np.nan, np.nan],
                "prcp": [5.0, 10.0],
                "latitude": [50.0, 51.0],
                "longitude": [8.0, 9.0],
                "elevation": [100, 200],
                "distance": [10, 20],
            },
            index=pd.MultiIndex.from_tuples(
                [(time, "A"), (time, "B")], names=["time", "station"]
            ),
        )

        point = Point(50.5, 8.5, 150)
        ts = self._create_mock_timeseries()

        idw_func = inverse_distance_weighting(power=2.0)
        result = idw_func(df, ts, point)

        assert not result.empty
        assert np.isnan(result["temp"].iloc[0])
        assert np.isfinite(result["prcp"].iloc[0])
