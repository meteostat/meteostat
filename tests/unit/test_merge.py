"""
Test merge functionality

The code is licensed under the MIT license.
"""

import pytest
import pandas as pd

from meteostat.api.merge import merge
from meteostat.api.timeseries import TimeSeries
from meteostat.enumerations import Granularity


class TestMerge:
    """Test merge() function for handling empty lists and combining TimeSeries"""

    def test_empty_list_raises_valueerror(self):
        """merge([]) should raise ValueError, not IndexError"""
        with pytest.raises(ValueError, match="[Cc]annot merge empty"):
            merge([])

    def test_single_item_list_works(self):
        """merge([ts]) with single item should return that item"""
        stations_df = pd.DataFrame(
            {"latitude": [50.0], "longitude": [8.0], "elevation": [100]},
            index=pd.Index(["TEST"], name="id"),
        )

        ts = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        result = merge([ts])
        assert result is not None
        assert result.granularity == Granularity.DAILY

    def test_two_compatible_timeseries_works(self):
        """merge([ts1, ts2]) with compatible timeseries should work"""
        stations_df = pd.DataFrame(
            {"latitude": [50.0], "longitude": [8.0], "elevation": [100]},
            index=pd.Index(["TEST"], name="id"),
        )

        ts1 = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        ts2 = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        result = merge([ts1, ts2])
        assert result is not None
        assert result.granularity == Granularity.DAILY

    def test_different_granularity_raises_valueerror(self):
        """merge() with different granularity should raise ValueError"""
        stations_df = pd.DataFrame(
            {"latitude": [50.0], "longitude": [8.0], "elevation": [100]},
            index=pd.Index(["TEST"], name="id"),
        )

        ts_daily = TimeSeries(
            granularity=Granularity.DAILY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        ts_hourly = TimeSeries(
            granularity=Granularity.HOURLY,
            stations=stations_df,
            df=None,
            start=None,
            end=None,
        )

        with pytest.raises(ValueError, match="divergent granularity"):
            merge([ts_daily, ts_hourly])
