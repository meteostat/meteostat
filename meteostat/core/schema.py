"""
Schema Service

The Schema Service provides methods to clean and format
DataFrames based on a set of parameters.
"""

from copy import copy
from inspect import isfunction
from typing import Callable, List

import pandas as pd

from meteostat.core.logger import logger
from meteostat.core.parameters import parameter_service
from meteostat.core.validator import Validator
from meteostat.enumerations import Granularity, Parameter, UnitSystem
from meteostat.utils.conversions import CONVERSION_MAPPINGS, to_condition, to_direction


class SchemaService:
    """
    Schema service
    """

    @staticmethod
    def _apply_validator(
        validator: Validator | Callable, df: pd.DataFrame, col: str
    ) -> pd.Series:
        """
        Apply a validator
        """
        if isfunction(validator):
            v: Validator = validator()  # type: ignore
        else:
            v = validator

        if not isinstance(v, Validator):
            return pd.Series(data=True, index=df.index, dtype=bool)

        if v.ignore_na:
            result = pd.Series(data=True, index=df.index, dtype=bool)
            test_result = v.test(
                df.loc[df[col].notnull()][col],
                df.loc[df[col].notnull()],
                col,
            )
            if isinstance(test_result, pd.Series):
                result.update(test_result)
            return result.astype(bool)

        test_result = v.test(df[col], df, col)
        if isinstance(test_result, bool):
            return pd.Series(data=test_result, index=df.index, dtype=bool)
        return test_result

    @staticmethod
    def purge(df: pd.DataFrame, parameters: List[Parameter]) -> pd.DataFrame:
        """
        Remove DataFrame columns which are not a known parameter
        """
        columns = [parameter for parameter in parameters if parameter in df.columns]
        return df[columns]

    @staticmethod
    def fill(df: pd.DataFrame, parameters: List[Parameter]) -> pd.DataFrame:
        """
        Add missing schema columns to DataFrame
        """
        for parameter_id in parameters:
            if parameter_id not in df:
                df[parameter_id] = None

        return df

    @staticmethod
    def format(df: pd.DataFrame, granularity: Granularity) -> pd.DataFrame:
        """
        Set data types and round values
        """
        temp = copy(df)

        for col in df.columns:
            parameter = parameter_service.get_parameter(col, granularity)

            if not parameter:
                logger.warning(
                    "Column %s is not a valid column name and won't be formatted", col
                )
                continue

            if "int" in str(parameter.dtype).lower():
                temp[col] = pd.to_numeric(temp[col]).round(0)

            temp[col] = temp[col].astype(parameter.dtype, errors="ignore")

            if "float" in str(parameter.dtype).lower():
                temp[col] = temp[col].round(1)

        return temp

    @classmethod
    def clean(
        cls, df: pd.DataFrame, granularity: Granularity, fill=None
    ) -> pd.DataFrame:
        """
        Remove invalid data from a DataFrame
        """
        temp = copy(df)

        for col in temp.columns:
            if "_source" in col:
                continue

            parameter = parameter_service.get_parameter(col, granularity)

            if not parameter:
                logger.warning(
                    "Column %s is not a valid column name and won't be cleaned", col
                )
                continue

            for validator in parameter.validators:
                test = cls._apply_validator(validator, temp, col)
                temp.loc[~test, col] = fill

        return temp

    def humanize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert wind direction and condition codes to human-readable values
        """
        temp = copy(df)

        if Parameter.WDIR in temp.columns:
            temp[Parameter.WDIR] = temp[Parameter.WDIR].apply(to_direction)

        if Parameter.COCO in temp.columns:
            temp[Parameter.COCO] = temp[Parameter.COCO].apply(to_condition)

        return temp

    @classmethod
    def convert(cls, df, granularity: Granularity, units: UnitSystem) -> pd.DataFrame:
        """
        Convert units in a DataFrame
        """
        temp = copy(df)

        for col in temp.columns:
            if "_source" in col:
                continue

            parameter = parameter_service.get_parameter(col, granularity)

            if not parameter:
                logger.warning(
                    "Column %s is not a valid column name and won't be converted", col
                )
                continue

            if parameter.unit in CONVERSION_MAPPINGS:
                if units in CONVERSION_MAPPINGS[parameter.unit]:
                    conversion_func = CONVERSION_MAPPINGS[parameter.unit][units]
                    temp[col] = temp[col].apply(conversion_func)

        return temp


schema_service = SchemaService()
