"""
Test validators module

The code is licensed under the MIT license.
"""

import pandas as pd
import numpy as np

from meteostat.utils.validators import minimum, maximum
from meteostat.core.validator import Validator


class TestMinimumValidator:
    """Test minimum validator function"""

    def test_minimum_basic(self):
        """Test minimum validator with basic values"""
        validator = minimum(10)
        assert isinstance(validator, Validator)

    def test_minimum_all_above(self):
        """Test minimum validator when all values are above minimum"""
        validator = minimum(10)
        series = pd.Series([11, 12, 20, 15])
        result = validator.func(series)
        assert result.all()

    def test_minimum_all_below(self):
        """Test minimum validator when all values are below minimum"""
        validator = minimum(10)
        series = pd.Series([1, 2, 3, 4])
        result = validator.func(series)
        assert not result.any()

    def test_minimum_mixed(self):
        """Test minimum validator with mixed values"""
        validator = minimum(10)
        series = pd.Series([5, 10, 15, 20])
        result = validator.func(series)
        assert result.tolist() == [False, True, True, True]

    def test_minimum_equal_to_threshold(self):
        """Test minimum validator with values equal to threshold"""
        validator = minimum(10)
        series = pd.Series([10, 10, 10])
        result = validator.func(series)
        assert result.all()

    def test_minimum_negative_threshold(self):
        """Test minimum validator with negative threshold"""
        validator = minimum(-5)
        series = pd.Series([-10, -5, 0, 5])
        result = validator.func(series)
        assert result.tolist() == [False, True, True, True]

    def test_minimum_float_threshold(self):
        """Test minimum validator with float threshold"""
        validator = minimum(10.5)
        series = pd.Series([10.4, 10.5, 10.6])
        result = validator.func(series)
        assert result.tolist() == [False, True, True]

    def test_minimum_with_none(self):
        """Test minimum validator with None values"""
        validator = minimum(10)
        series = pd.Series([5, None, 15, np.nan])
        result = validator.func(series)
        # None and NaN should evaluate to False
        assert not result.tolist()[1] or pd.isna(result.tolist()[1])
        assert not result.tolist()[3] or pd.isna(result.tolist()[3])

    def test_minimum_with_nan(self):
        """Test minimum validator with NaN values"""
        validator = minimum(10)
        series = pd.Series([15, np.nan])
        result = validator.func(series)
        assert pd.isna(result.tolist()[1]) or not result.tolist()[1]


class TestMaximumValidator:
    """Test maximum validator function"""

    def test_maximum_basic(self):
        """Test maximum validator with basic values"""
        validator = maximum(20)
        assert isinstance(validator, Validator)

    def test_maximum_all_below(self):
        """Test maximum validator when all values are below maximum"""
        validator = maximum(20)
        series = pd.Series([1, 5, 10, 15])
        result = validator.func(series)
        assert result.all()

    def test_maximum_all_above(self):
        """Test maximum validator when all values are above maximum"""
        validator = maximum(20)
        series = pd.Series([21, 25, 30, 50])
        result = validator.func(series)
        assert not result.any()

    def test_maximum_mixed(self):
        """Test maximum validator with mixed values"""
        validator = maximum(20)
        series = pd.Series([5, 20, 25, 30])
        result = validator.func(series)
        assert result.tolist() == [True, True, False, False]

    def test_maximum_equal_to_threshold(self):
        """Test maximum validator with values equal to threshold"""
        validator = maximum(20)
        series = pd.Series([20, 20, 20])
        result = validator.func(series)
        assert result.all()

    def test_maximum_negative_threshold(self):
        """Test maximum validator with negative threshold"""
        validator = maximum(-5)
        series = pd.Series([-10, -5, 0, 5])
        result = validator.func(series)
        assert result.tolist() == [True, True, False, False]

    def test_maximum_float_threshold(self):
        """Test maximum validator with float threshold"""
        validator = maximum(10.5)
        series = pd.Series([10.4, 10.5, 10.6])
        result = validator.func(series)
        assert result.tolist() == [True, True, False]

    def test_maximum_with_none(self):
        """Test maximum validator with None values"""
        validator = maximum(20)
        series = pd.Series([10, None, 25, np.nan])
        result = validator.func(series)
        # None and NaN should evaluate to False
        assert not result.tolist()[1] or pd.isna(result.tolist()[1])
        assert not result.tolist()[3] or pd.isna(result.tolist()[3])

    def test_maximum_with_nan(self):
        """Test maximum validator with NaN values"""
        validator = maximum(20)
        series = pd.Series([15, np.nan])
        result = validator.func(series)
        assert pd.isna(result.tolist()[1]) or not result.tolist()[1]


class TestValidatorChaining:
    """Test combining multiple validators"""

    def test_minimum_and_maximum_valid_range(self):
        """Test values within minimum and maximum range"""
        min_validator = minimum(10)
        max_validator = maximum(20)
        series = pd.Series([5, 10, 15, 20, 25])

        min_result = min_validator.func(series)
        max_result = max_validator.func(series)
        combined = min_result & max_result

        assert combined.tolist() == [False, True, True, True, False]

    def test_validators_with_large_dataset(self):
        """Test validators with larger dataset"""
        validator = minimum(0)
        series = pd.Series(range(-50, 51))
        result = validator.func(series)

        # First 50 values should be False (< 0)
        # Last 51 values should be True (>= 0)
        assert sum(result) == 51

    def test_multiple_validators_intersection(self):
        """Test intersection of multiple validators"""
        min_val = minimum(5)
        max_val = maximum(15)
        series = pd.Series([3, 5, 10, 15, 20])

        min_result = min_val.func(series)
        max_result = max_val.func(series)
        result = min_result & max_result

        assert result.tolist() == [False, True, True, True, False]
