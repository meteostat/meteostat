"""
Tests for large request blocking functionality

Tests the check that blocks requests with a time range longer than 30 years
or more than 10 stations when `config.block_large_requests` is `True`.
"""

from datetime import datetime

import pytest

import meteostat as ms
from meteostat.api.config import config


class TestLargeTimeRangeBlocking:
    """
    Tests for blocking large requests based on time range
    """

    def test_large_request_blocked_by_default(self, mock_stations_database):
        """
        Large requests (>30 years) should be blocked by default
        """
        # config.block_large_requests is True by default
        assert config.block_large_requests is True

        # Request spanning 31 years should raise ValueError
        with pytest.raises(
            ValueError, match="Daily requests longer than 30 years are blocked"
        ):
            ts = ms.daily("10637", datetime(1990, 1, 1), datetime(2021, 12, 31))
            ts.fetch()

    def test_large_request_exactly_30_years_allowed(
        self, mocker, mock_stations_database
    ):
        """
        Requests spanning exactly 30 years should be allowed
        """
        # Mock the provider to avoid None result
        mocker.patch(
            "meteostat.providers.meteostat.daily.fetch",
            return_value=mocker.MagicMock(empty=True),
        )

        # Request spanning exactly 30 years (1990-2020)
        ts = ms.daily("10637", datetime(1990, 1, 1), datetime(2020, 12, 31))
        # Should not raise an exception (year difference is exactly 30)
        ts.fetch()  # Just verify it doesn't raise

    def test_large_request_just_over_30_years_blocked(self, mock_stations_database):
        """
        Requests spanning just over 30 years should be blocked
        """
        # Request spanning 31 years (1990-2021)
        with pytest.raises(
            ValueError, match="Daily requests longer than 30 years are blocked"
        ):
            ts = ms.daily("10637", datetime(1990, 1, 1), datetime(2021, 1, 1))
            ts.fetch()

    def test_small_request_allowed(self, mock_daily_fetch, mock_stations_database):
        """
        Small requests (<30 years) should always be allowed
        """
        # Request spanning 5 years
        ts = ms.daily("10637", datetime(2019, 1, 1), datetime(2024, 12, 31))
        df = ts.fetch()
        assert df is not None

    def test_one_year_request_allowed(self, mock_daily_fetch, mock_stations_database):
        """
        One-year requests should be allowed
        """
        ts = ms.daily("10637", datetime(2024, 1, 1), datetime(2024, 12, 31))
        df = ts.fetch()
        assert df is not None

    def test_single_day_request_allowed(self, mock_daily_fetch, mock_stations_database):
        """
        Single-day requests should be allowed
        """
        ts = ms.daily("10637", datetime(2024, 1, 15), datetime(2024, 1, 15))
        df = ts.fetch()
        assert df is not None

    def test_request_with_none_start_date(self, mock_stations_database):
        """
        Requests with None start date should be blocked
        """
        # When start is None, the check should block the request
        # This tests the condition: req.start is None
        with pytest.raises(
            ValueError,
            match="Hourly and daily requests without a start date are blocked",
        ):
            ts = ms.daily("10637", None, datetime(2024, 12, 31))
            ts.fetch()

    def test_request_with_none_end_date_allowed(
        self, mock_daily_fetch, mock_stations_database
    ):
        """
        Requests with None end date should be allowed (uses datetime.now())
        """
        # When end is None, it uses datetime.now() for validation
        # Request from 5 years ago to now should be allowed for daily
        current_year = datetime.now().year
        ts = ms.daily("10637", datetime(current_year - 5, 1, 1), None)
        df = ts.fetch()
        assert df is not None

    def test_request_with_both_dates_none(self, mock_stations_database):
        """
        Requests without a start date should be blocked
        """
        with pytest.raises(
            ValueError,
            match="Hourly and daily requests without a start date are blocked",
        ):
            ts = ms.daily("10637", None, None)
            ts.fetch()

    def test_large_request_allowed_when_config_disabled(
        self, mocker, mock_stations_database
    ):
        """
        Large requests should be allowed when config.block_large_requests is False
        """
        # Mock the provider to avoid None result
        mocker.patch(
            "meteostat.providers.meteostat.daily.fetch",
            return_value=mocker.MagicMock(empty=True),
        )

        # Temporarily disable the blocking
        original_value = config.block_large_requests
        config.block_large_requests = False

        try:
            # Request spanning 31 years should not raise an exception
            ts = ms.daily("10637", datetime(1990, 1, 1), datetime(2021, 12, 31))
            ts.fetch()  # Just verify it doesn't raise
        finally:
            # Restore original config value
            config.block_large_requests = original_value

    def test_config_message_mentions_setting(self, mock_stations_database):
        """
        Error message should mention how to disable the check
        """
        with pytest.raises(
            ValueError, match="set `config.block_large_requests = False`"
        ):
            ts = ms.daily("10637", datetime(1990, 1, 1), datetime(2021, 12, 31))
            ts.fetch()

    def test_boundary_year_calculation_1970_2000(self, mocker, mock_stations_database):
        """
        Test exact boundary: 1970-2000 (30 years, should be allowed)
        """
        # Mock the provider to avoid None result
        mocker.patch(
            "meteostat.providers.meteostat.daily.fetch",
            return_value=mocker.MagicMock(empty=True),
        )

        ts = ms.daily("10637", datetime(1970, 1, 1), datetime(2000, 12, 31))
        ts.fetch()  # Just verify it doesn't raise

    def test_boundary_year_calculation_1970_2001(self, mock_stations_database):
        """
        Test just over boundary: 1970-2001 (31 years, should be blocked)
        """
        with pytest.raises(
            ValueError, match="Daily requests longer than 30 years are blocked"
        ):
            ts = ms.daily("10637", datetime(1970, 1, 1), datetime(2001, 1, 1))
            ts.fetch()

    def test_hourly_request_large_time_range_blocked(self, mock_stations_database):
        """
        Hourly requests longer than 3 years should be blocked
        """
        with pytest.raises(
            ValueError, match="Hourly requests longer than 3 years are blocked"
        ):
            ts = ms.hourly("10637", datetime(2015, 1, 1), datetime(2021, 12, 31))
            ts.fetch()

    def test_hourly_request_3_years_allowed(
        self, mock_daily_fetch, mock_stations_database
    ):
        """
        Hourly requests with exactly 3 years should be allowed
        """
        ts = ms.hourly("10637", datetime(2019, 1, 1), datetime(2022, 12, 31))
        df = ts.fetch()
        assert df is not None

    def test_hourly_request_over_3_years_blocked(self, mock_stations_database):
        """
        Hourly requests over 3 years should be blocked
        """
        with pytest.raises(
            ValueError, match="Hourly requests longer than 3 years are blocked"
        ):
            ts = ms.hourly("10637", datetime(2018, 1, 1), datetime(2024, 12, 31))
            ts.fetch()

    def test_monthly_request_large_time_range_allowed(
        self, mock_daily_fetch, mock_stations_database
    ):
        """
        Monthly requests do not have time range validation (no limit enforced)
        """
        # Monthly requests are allowed regardless of time range (no validation)
        ts = ms.monthly("10637", datetime(1990, 1, 1), datetime(2021, 12, 31))
        df = ts.fetch()
        assert df is not None

    def test_normals_request_large_time_range_allowed(
        self, mock_daily_fetch, mock_stations_database
    ):
        """
        Normals requests do not have time range validation (no limit enforced)
        """
        # Normals requests are allowed regardless of time range (no validation)
        ts = ms.normals("10637", 1990, 2021)
        df = ts.fetch()
        assert df is not None

    def test_leap_year_spanning_30_years(self, mocker, mock_stations_database):
        """
        Test with leap years included in 30-year span
        """
        # Mock the provider to avoid None result
        mocker.patch(
            "meteostat.providers.meteostat.daily.fetch",
            return_value=mocker.MagicMock(empty=True),
        )

        # 2000 and 2020 are leap years in this range
        ts = ms.daily("10637", datetime(1992, 2, 29), datetime(2022, 2, 28))
        ts.fetch()  # Just verify it doesn't raise

    def test_year_difference_calculation_dec_to_jan(
        self, mock_daily_fetch, mock_stations_database
    ):
        """
        Test year difference calculation across calendar years
        """
        # Dec 31, 1994 to Jan 1, 2025 = 30 year difference (allowed)
        ts = ms.daily("10637", datetime(1994, 12, 31), datetime(2024, 12, 31))
        df = ts.fetch()
        assert df is not None


class TestLargeStationCountBlocking:
    """
    Tests for blocking requests with more than 10 stations
    """

    def test_single_station_allowed(self, mock_daily_fetch, mock_stations_database):
        """
        Single station requests should always be allowed
        """
        ts = ms.daily("10637", datetime(2024, 1, 1), datetime(2024, 12, 31))
        df = ts.fetch()
        assert df is not None

    def test_10_stations_allowed(self, mocker, mock_stations_database):
        """
        Requests with exactly 10 stations should be allowed
        """
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=10)

        # Mock the provider
        mocker.patch(
            "meteostat.core.providers.provider_service.fetch_data",
            return_value=mocker.MagicMock(empty=True),
        )

        # This should not raise an exception (10 stations is at the limit)
        ts = ms.daily(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
        ts.fetch()  # Just verify it doesn't raise

    def test_multiple_stations_just_over_limit(self, mock_stations_database):
        """
        Requests with more than 10 stations should be blocked by default
        """
        # config.block_large_requests is True by default
        assert config.block_large_requests is True

        # Create a list of 11 station IDs
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=11)

        # Request with 11 stations should raise ValueError
        with pytest.raises(
            ValueError, match="Requests with more than 10 stations are blocked"
        ):
            ts = ms.daily(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()

    def test_many_stations_blocked(self, mock_stations_database):
        """
        Requests with many stations should be blocked
        """
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=50)

        with pytest.raises(
            ValueError, match="Requests with more than 10 stations are blocked"
        ):
            ts = ms.daily(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()

    def test_large_station_count_allowed_when_config_disabled(
        self, mocker, mock_stations_database
    ):
        """
        Large station requests should be allowed when config.block_large_requests is False
        """
        # Create a list of 11 valid station IDs (using the same valid station repeated)
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=11)

        # Mock the provider
        mocker.patch(
            "meteostat.core.providers.provider_service.fetch_data",
            return_value=mocker.MagicMock(empty=True),
        )

        # Temporarily disable the blocking
        original_value = config.block_large_requests
        config.block_large_requests = False

        try:
            # Request with 11 stations should not raise an exception
            ts = ms.daily(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()  # Just verify it doesn't raise
        finally:
            # Restore original config value
            config.block_large_requests = original_value

    def test_station_count_message_mentions_setting(self, mock_stations_database):
        """
        Error message for station count should mention how to disable the check
        """
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=15)

        with pytest.raises(
            ValueError, match="set `config.block_large_requests = False`"
        ):
            ts = ms.daily(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()

    def test_station_count_check_for_hourly(self, mock_stations_database):
        """
        Station count check should also apply to hourly data
        """
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=11)

        with pytest.raises(
            ValueError, match="Requests with more than 10 stations are blocked"
        ):
            ts = ms.hourly(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()

    def test_station_count_check_for_monthly(self, mock_stations_database):
        """
        Station count check should also apply to monthly data
        """
        station_ids = ms.stations.nearby(ms.Point(50, 8), limit=11)

        with pytest.raises(
            ValueError, match="Requests with more than 10 stations are blocked"
        ):
            ts = ms.monthly(station_ids, datetime(2024, 1, 1), datetime(2024, 12, 31))
            ts.fetch()
