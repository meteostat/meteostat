"""
Dummy provider module for testing ProviderService.fetch_data() dispatch
"""

import pandas as pd

from meteostat.typing import ProviderRequest


def fetch(query: ProviderRequest) -> pd.DataFrame:
    return pd.DataFrame({"temp": [20.0]})
