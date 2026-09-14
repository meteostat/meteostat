"""
Test SchemaService

The code is licensed under the MIT license.
"""

import pandas as pd

from meteostat.core.schema import schema_service
from meteostat.enumerations import Granularity, Parameter


class TestSchemaServiceFormat:
    """Test SchemaService.format function"""

    def test_format_handles_unconvertible_dtype(self):
        """Test that format() silently skips columns that cannot be cast"""
        # Simulate a column with non-numeric strings that cannot be cast to Float64
        df = pd.DataFrame(
            {Parameter.TEMP: ["not-a-number", "also-invalid"]},
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="time"),
        )

        # Should not raise; the except (TypeError, ValueError) branch keeps original values
        result = schema_service.format(df, Granularity.DAILY)
        assert isinstance(result, pd.DataFrame)
        assert Parameter.TEMP in result.columns
