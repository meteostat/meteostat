"""
Inventory Module

Provides classes for working with weather station data inventories.
"""

from datetime import date, datetime
from typing import List, Optional

import pandas as pd

from meteostat.enumerations import Parameter


class Inventory:
    """
    A weather station's data inventory
    """

    df: Optional[pd.DataFrame] = None

    def __init__(self, df: Optional[pd.DataFrame] = None):
        if df is not None and not df.empty:
            self.df = df

    @property
    def start(self) -> Optional[date]:
        """
        Get the earliest start date from the inventory
        """
        return (
            datetime.strptime(self.df["start"].min(), "%Y-%m-%d").date()
            if self.df is not None
            else None
        )

    @property
    def end(self) -> Optional[date]:
        """
        Get the latest end date from the inventory
        """
        return (
            datetime.strptime(self.df["end"].max(), "%Y-%m-%d").date()
            if self.df is not None
            else None
        )

    @property
    def parameters(self) -> Optional[List[Parameter]]:
        """
        Get the list of available parameters from the inventory
        """
        if self.df is None:
            return []

        return [
            Parameter[parameter.upper()]
            for parameter in self.df.index.get_level_values("parameter").unique()
        ]
