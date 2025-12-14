"""
Extended test for parsers module - time parsing functions

The code is licensed under the MIT license.
"""

from datetime import datetime, date

import pytz

from meteostat.utils.parsers import parse_time, parse_month, parse_year


class TestParseTime:
    """Test parse_time function"""

    def test_parse_time_with_none(self):
        """Test parse_time returns None for None input"""
        result = parse_time(None)
        assert result is None

    def test_parse_time_with_date(self):
        """Test parse_time with date object"""
        input_date = date(2020, 1, 15)
        result = parse_time(input_date)

        assert isinstance(result, datetime)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_time_with_date_is_end(self):
        """Test parse_time with date and is_end=True"""
        input_date = date(2020, 1, 15)
        result = parse_time(input_date, is_end=True)

        assert isinstance(result, datetime)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_parse_time_with_datetime(self):
        """Test parse_time with datetime object"""
        input_dt = datetime(2020, 1, 15, 12, 30, 45)
        result = parse_time(input_dt)

        assert result == input_dt

    def test_parse_time_with_datetime_and_timezone(self):
        """Test parse_time with datetime and timezone conversion"""
        # Create a datetime in Berlin timezone
        tz_berlin = pytz.timezone("Europe/Berlin")
        input_dt = tz_berlin.localize(datetime(2020, 1, 15, 12, 0, 0))

        result = parse_time(input_dt, timezone="Europe/Berlin")

        assert isinstance(result, datetime)
        assert result.tzinfo is None  # Result should be in UTC without tzinfo

    def test_parse_time_with_date_and_timezone(self):
        """Test parse_time with date and timezone"""
        input_date = date(2020, 1, 15)
        result = parse_time(input_date, timezone="Europe/London")

        assert isinstance(result, datetime)
        assert result.year == 2020

    def test_parse_time_empty_string(self):
        """Test parse_time with empty string"""
        result = parse_time("")  # type: ignore[arg-type]
        assert result is None

    def test_parse_time_zero(self):
        """Test parse_time with zero (falsy value)"""
        result = parse_time(0)  # type: ignore[arg-type]
        assert result is None


class TestParseMonth:
    """Test parse_month function"""

    def test_parse_month_with_none(self):
        """Test parse_month returns None for None input"""
        result = parse_month(None)
        assert result is None

    def test_parse_month_first_day(self):
        """Test parse_month returns first day of month"""
        input_date = date(2020, 1, 15)
        result = parse_month(input_date)

        assert isinstance(result, date)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 1

    def test_parse_month_last_day(self):
        """Test parse_month with is_end=True returns last day"""
        input_date = date(2020, 1, 15)
        result = parse_month(input_date, is_end=True)

        assert isinstance(result, date)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 31

    def test_parse_month_february_non_leap(self):
        """Test parse_month for February in non-leap year"""
        input_date = date(2021, 2, 15)
        result = parse_month(input_date, is_end=True)

        assert isinstance(result, date)
        assert result.month == 2
        assert result.day == 28

    def test_parse_month_february_leap_year(self):
        """Test parse_month for February in leap year"""
        input_date = date(2020, 2, 15)
        result = parse_month(input_date, is_end=True)

        assert isinstance(result, date)
        assert result.month == 2
        assert result.day == 29

    def test_parse_month_december_last_day(self):
        """Test parse_month for December"""
        input_date = date(2020, 12, 15)
        result = parse_month(input_date, is_end=True)

        assert isinstance(result, date)
        assert result.month == 12
        assert result.day == 31

    def test_parse_month_with_datetime(self):
        """Test parse_month with datetime object"""
        input_dt = datetime(2020, 3, 15, 12, 30)
        result = parse_month(input_dt)

        assert isinstance(result, date)
        assert result.year == 2020
        assert result.month == 3
        assert result.day == 1

    def test_parse_month_preserves_year_and_month(self):
        """Test that parse_month preserves year and month"""
        for month in range(1, 13):
            input_date = date(2020, month, 15)
            result = parse_month(input_date)
            assert isinstance(result, date)
            assert result.year == 2020
            assert result.month == month


class TestParseYear:
    """Test parse_year function"""

    def test_parse_year_first_day(self):
        """Test parse_year returns first day of year"""
        result = parse_year(2020)

        assert isinstance(result, date)
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 1

    def test_parse_year_last_day(self):
        """Test parse_year with is_end=True returns last day"""
        result = parse_year(2020, is_end=True)

        assert isinstance(result, date)
        assert result.year == 2020
        assert result.month == 12
        assert result.day == 31

    def test_parse_year_leap_year(self):
        """Test parse_year with leap year"""
        result = parse_year(2020, is_end=True)

        assert result.year == 2020
        assert result.month == 12
        assert result.day == 31

    def test_parse_year_non_leap_year(self):
        """Test parse_year with non-leap year"""
        result = parse_year(2021, is_end=True)

        assert result.year == 2021
        assert result.month == 12
        assert result.day == 31

    def test_parse_year_multiple_years(self):
        """Test parse_year for multiple different years"""
        for year in [2000, 2010, 2020, 2021, 2099]:
            result = parse_year(year)
            assert result.year == year
            assert result.month == 1
            assert result.day == 1

    def test_parse_year_is_end_multiple_years(self):
        """Test parse_year with is_end for multiple years"""
        for year in [2000, 2010, 2020, 2021, 2099]:
            result = parse_year(year, is_end=True)
            assert result.year == year
            assert result.month == 12
            assert result.day == 31
