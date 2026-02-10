"""
Test lapse rate function

The code is licensed under the MIT license.
"""

import numpy as np
import pandas as pd
import pytest

from meteostat.enumerations import Parameter
from meteostat.interpolation.lapserate import apply_lapse_rate


class TestLapseRateNaNHandling:
    """Test that apply_lapse_rate properly handles NaN values."""

    def test_nan_values_remain_nan_after_lapse_rate(self):
        """
        NaN temperature values should remain NaN after lapse rate adjustment.
        """
        df = pd.DataFrame(
            {
                Parameter.TEMP: [20.0, np.nan, 22.0, np.nan, 24.0],
                "elevation": [100, 100, 100, 100, 100],
            }
        )

        result = apply_lapse_rate(df.copy(), elevation=200, lapse_rate=6.5)

        # NaN positions should still be NaN
        assert pd.isna(result[Parameter.TEMP].iloc[1]), (
            f"NaN at index 1 should remain NaN, got {result[Parameter.TEMP].iloc[1]}"
        )
        assert pd.isna(result[Parameter.TEMP].iloc[3]), (
            f"NaN at index 3 should remain NaN, got {result[Parameter.TEMP].iloc[3]}"
        )

    def test_valid_values_are_adjusted(self):
        """
        Non-NaN temperature values should be adjusted by lapse rate.
        """
        df = pd.DataFrame(
            {
                Parameter.TEMP: [20.0, 22.0],
                "elevation": [100, 100],
            }
        )

        result = apply_lapse_rate(df.copy(), elevation=200, lapse_rate=6.5)

        # Values should be adjusted (not NaN)
        assert pd.notna(result[Parameter.TEMP].iloc[0])
        assert pd.notna(result[Parameter.TEMP].iloc[1])

        # Adjustment: (6.5 / 1000) * (100 - 200) = -0.65
        # So temps should decrease by 0.65
        assert result[Parameter.TEMP].iloc[0] == pytest.approx(19.4, abs=0.1)
        assert result[Parameter.TEMP].iloc[1] == pytest.approx(21.4, abs=0.1)


class TestLapseRateBasicFunctionality:
    """Test basic lapse rate functionality."""

    def test_lapse_rate_adjustment_formula(self):
        """
        Test that lapse rate adjustment follows the correct formula.
        """
        df = pd.DataFrame(
            {
                Parameter.TEMP: [20.0],
                "elevation": [100],
            }
        )

        # Higher target elevation - temperature should decrease
        result = apply_lapse_rate(df.copy(), elevation=1100, lapse_rate=6.5)
        # Adjustment: (6.5 / 1000) * (100 - 1100) = -6.5
        assert result[Parameter.TEMP].iloc[0] == pytest.approx(13.5, abs=0.1)

        # Lower target elevation - temperature should increase
        df_low = pd.DataFrame(
            {
                Parameter.TEMP: [20.0],
                "elevation": [1000],
            }
        )
        result_low = apply_lapse_rate(df_low.copy(), elevation=0, lapse_rate=6.5)
        # Adjustment: (6.5 / 1000) * (1000 - 0) = 6.5
        assert result_low[Parameter.TEMP].iloc[0] == pytest.approx(26.5, abs=0.1)

    def test_lapse_rate_with_all_nan(self):
        """
        Test that all-NaN columns remain all-NaN.
        """
        df = pd.DataFrame(
            {
                Parameter.TEMP: [np.nan, np.nan, np.nan],
                "elevation": [100, 100, 100],
            }
        )

        result = apply_lapse_rate(df.copy(), elevation=200, lapse_rate=6.5)

        assert pd.isna(result[Parameter.TEMP]).all()

    def test_lapse_rate_preserves_other_columns(self):
        """
        Test that lapse rate adjustment doesn't affect non-temperature columns.
        """
        df = pd.DataFrame(
            {
                Parameter.TEMP: [20.0],
                Parameter.PRCP: [5.0],
                "elevation": [100],
            }
        )

        result = apply_lapse_rate(df.copy(), elevation=200, lapse_rate=6.5)

        # Precipitation should be unchanged
        assert result[Parameter.PRCP].iloc[0] == 5.0
