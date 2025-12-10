"""
Schema Column Validator

This class is used to validate DataFrame columns based
on a parameter specification.
"""

from inspect import signature
from typing import Callable

from pandas import DataFrame, Series


class Validator:
    """
    Schema Column Validator
    """

    func: Callable
    ignore_na = False
    is_relational = False

    def __init__(self, func: Callable, ignore_na=False, is_relational=False):
        self.func = func
        self.ignore_na = ignore_na
        self.is_relational = is_relational

    def test(self, series: Series, df: DataFrame, column: str) -> bool | Series:
        """
        Run validator

        Returns a bool series:
        True -> Check passed
        False -> Check failed
        """
        arg_count = len((signature(self.func)).parameters)
        args = [series, df, column]
        return self.func(*args[0:arg_count])
