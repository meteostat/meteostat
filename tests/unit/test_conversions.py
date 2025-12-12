"""
Test conversions module

The code is licensed under the MIT license.
"""

from meteostat.utils.conversions import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    millimeters_to_inches,
    centimeters_to_inches,
    meters_to_feet,
    kmh_to_ms,
    kmh_to_mph,
    kelvin_to_celsius,
    ms_to_kmh,
    temp_dwpt_to_rhum,
    pres_to_msl,
    percentage_to_okta,
    jcm2_to_wm2,
    to_direction,
    to_condition,
)


class TestTemperatureConversions:
    """Test temperature conversion functions"""

    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion"""
        assert celsius_to_fahrenheit(0) == 32.0
        assert celsius_to_fahrenheit(100) == 212.0
        assert celsius_to_fahrenheit(-40) == -40.0
        assert celsius_to_fahrenheit(20) == 68.0

    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion"""
        assert celsius_to_kelvin(0) == 273.1
        assert celsius_to_kelvin(100) == 373.1
        assert celsius_to_kelvin(-273.15) == 0.0
        assert celsius_to_kelvin(20) == 293.1

    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion"""
        assert kelvin_to_celsius(273.15) == 0.0
        assert kelvin_to_celsius(373.15) == 100.0
        assert kelvin_to_celsius(293.15) == 20.0

    def test_kelvin_to_celsius_with_none(self):
        """Test Kelvin to Celsius conversion with None"""
        assert kelvin_to_celsius(None) is None

    def test_kelvin_to_celsius_with_nan(self):
        """Test Kelvin to Celsius conversion with NaN"""
        import numpy as np

        assert kelvin_to_celsius(np.nan) is None


class TestDistanceConversions:
    """Test distance conversion functions"""

    def test_millimeters_to_inches(self):
        """Test millimeters to inches conversion"""
        assert millimeters_to_inches(25.4) == 1.0
        assert millimeters_to_inches(254) == 10.0
        assert millimeters_to_inches(0) == 0.0

    def test_centimeters_to_inches(self):
        """Test centimeters to inches conversion"""
        assert centimeters_to_inches(2.54) == 1.0
        assert centimeters_to_inches(25.4) == 10.0
        assert centimeters_to_inches(0) == 0.0

    def test_meters_to_feet(self):
        """Test meters to feet conversion"""
        assert meters_to_feet(0.3048) == 1.0
        assert meters_to_feet(1) == 3.3
        assert meters_to_feet(10) == 32.8
        assert meters_to_feet(0) == 0.0


class TestSpeedConversions:
    """Test speed conversion functions"""

    def test_kmh_to_ms(self):
        """Test kilometers per hour to meters per second conversion"""
        assert kmh_to_ms(0) == 0.0
        assert kmh_to_ms(3.6) == 1.0
        assert kmh_to_ms(36) == 10.0
        assert kmh_to_ms(100) == 27.8

    def test_kmh_to_mph(self):
        """Test kilometers per hour to miles per hour conversion"""
        assert kmh_to_mph(0) == 0.0
        assert kmh_to_mph(1.609) == 1.0
        assert kmh_to_mph(100) == 62.1
        assert kmh_to_mph(50) == 31.1

    def test_ms_to_kmh(self):
        """Test meters per second to kilometers per hour conversion"""
        assert ms_to_kmh(0) == 0.0
        assert ms_to_kmh(1) == 3.6
        assert ms_to_kmh(10) == 36.0

    def test_ms_to_kmh_with_none(self):
        """Test meters per second to kilometers per hour with None"""
        assert ms_to_kmh(None) is None

    def test_ms_to_kmh_with_nan(self):
        """Test meters per second to kilometers per hour with NaN"""
        import numpy as np

        assert ms_to_kmh(np.nan) is None


class TestHumidityConversions:
    """Test humidity calculation functions"""

    def test_temp_dwpt_to_rhum_basic(self):
        """Test relative humidity calculation from temperature and dew point"""
        # Test with equal temp and dew point (100% humidity)
        row = {"temp": 20.0, "dwpt": 20.0}
        result = temp_dwpt_to_rhum(row)
        assert abs(result - 100.0) < 0.1

    def test_temp_dwpt_to_rhum_typical(self):
        """Test typical relative humidity calculation"""
        # Typical case: temperature = 20°C, dew point = 10°C
        row = {"temp": 20.0, "dwpt": 10.0}
        result = temp_dwpt_to_rhum(row)
        assert 50 < result < 65  # Reasonable range

    def test_temp_dwpt_to_rhum_with_none_temp(self):
        """Test relative humidity calculation with None temperature"""
        row = {"temp": None, "dwpt": 10.0}
        result = temp_dwpt_to_rhum(row)
        assert result is None

    def test_temp_dwpt_to_rhum_with_none_dwpt(self):
        """Test relative humidity calculation with None dew point"""
        row = {"temp": 20.0, "dwpt": None}
        result = temp_dwpt_to_rhum(row)
        assert result is None


class TestPressureConversions:
    """Test pressure conversion functions"""

    def test_pres_to_msl_basic(self):
        """Test local pressure to mean sea level conversion"""
        row = {"pres": 900.0, "temp": 15.0}
        result = pres_to_msl(row, altitude=500, temp="temp")
        assert result is not None
        assert isinstance(result, (int, float))
        assert result > 900.0  # MSL should be higher than local

    def test_pres_to_msl_without_altitude(self):
        """Test pressure conversion returns None without altitude"""
        row = {"pres": 900.0, "temp": 15.0}
        result = pres_to_msl(row, altitude=None, temp="temp")
        assert result is None

    def test_pres_to_msl_with_invalid_pressure(self):
        """Test pressure conversion with invalid pressure value"""
        row = {"pres": -999, "temp": 15.0}
        result = pres_to_msl(row, altitude=500, temp="temp")
        assert result is None

    def test_pres_to_msl_without_temperature(self):
        """Test pressure conversion without temperature"""
        row = {"pres": 900.0, "temp": None}
        result = pres_to_msl(row, altitude=500, temp="temp")
        assert result is None

    def test_pres_to_msl_without_pressure(self):
        """Test pressure conversion without pressure"""
        row = {"pres": None, "temp": 15.0}
        result = pres_to_msl(row, altitude=500, temp="temp")
        assert result is None


class TestCloudCoverConversions:
    """Test cloud cover conversion functions"""

    def test_percentage_to_okta_clear(self):
        """Test percentage to okta conversion for clear sky"""
        assert percentage_to_okta(0) == 0
        assert percentage_to_okta(6) == 0

    def test_percentage_to_okta_overcast(self):
        """Test percentage to okta conversion for overcast"""
        assert percentage_to_okta(100) == 8
        assert percentage_to_okta(94) == 8

    def test_percentage_to_okta_partial(self):
        """Test percentage to okta conversion for partial cloud cover"""
        assert percentage_to_okta(50) == 4

    def test_percentage_to_okta_with_none(self):
        """Test percentage to okta conversion with None"""
        assert percentage_to_okta(None) is None

    def test_percentage_to_okta_with_nan(self):
        """Test percentage to okta conversion with NaN"""
        import numpy as np

        assert percentage_to_okta(np.nan) is None


class TestRadiationConversions:
    """Test radiation conversion functions"""

    def test_jcm2_to_wm2_basic(self):
        """Test joule per cm² to watt per m² conversion"""
        result = jcm2_to_wm2(100)
        assert result == 278

    def test_jcm2_to_wm2_zero(self):
        """Test joule per cm² to watt per m² conversion with zero"""
        assert jcm2_to_wm2(0) == 0

    def test_jcm2_to_wm2_with_none(self):
        """Test joule per cm² to watt per m² conversion with None"""
        assert jcm2_to_wm2(None) is None

    def test_jcm2_to_wm2_with_nan(self):
        """Test joule per cm² to watt per m² conversion with NaN"""
        import numpy as np

        assert jcm2_to_wm2(np.nan) is None


class TestWindDirectionConversions:
    """Test wind direction conversion functions"""

    def test_to_direction_north(self):
        """Test wind direction conversion for north"""
        assert to_direction(0) == "N"
        assert to_direction(359) == "N"
        assert to_direction(23) == "N"

    def test_to_direction_northeast(self):
        """Test wind direction conversion for northeast"""
        assert to_direction(45) == "NE"
        assert to_direction(24) == "NE"
        assert to_direction(68) == "NE"

    def test_to_direction_east(self):
        """Test wind direction conversion for east"""
        assert to_direction(90) == "E"
        assert to_direction(69) == "E"
        assert to_direction(113) == "E"

    def test_to_direction_southeast(self):
        """Test wind direction conversion for southeast"""
        assert to_direction(135) == "SE"
        assert to_direction(114) == "SE"
        assert to_direction(158) == "SE"

    def test_to_direction_south(self):
        """Test wind direction conversion for south"""
        assert to_direction(180) == "S"
        assert to_direction(159) == "S"
        assert to_direction(203) == "S"

    def test_to_direction_southwest(self):
        """Test wind direction conversion for southwest"""
        assert to_direction(225) == "SW"
        assert to_direction(204) == "SW"
        assert to_direction(248) == "SW"

    def test_to_direction_west(self):
        """Test wind direction conversion for west"""
        assert to_direction(270) == "W"
        assert to_direction(249) == "W"
        assert to_direction(293) == "W"

    def test_to_direction_northwest(self):
        """Test wind direction conversion for northwest"""
        assert to_direction(315) == "NW"
        assert to_direction(294) == "NW"
        assert to_direction(336) == "NW"

    def test_to_direction_boundary(self):
        """Test wind direction conversion at boundaries"""
        assert to_direction(337) == "N"


class TestWeatherConditionConversions:
    """Test weather condition conversion functions"""

    def test_to_condition_clear(self):
        """Test weather condition conversion for clear"""
        assert to_condition(1) == "Clear"

    def test_to_condition_fair(self):
        """Test weather condition conversion for fair"""
        assert to_condition(2) == "Fair"

    def test_to_condition_cloudy(self):
        """Test weather condition conversion for cloudy"""
        assert to_condition(3) == "Cloudy"

    def test_to_condition_rain(self):
        """Test weather condition conversion for rain"""
        assert to_condition(8) == "Rain"

    def test_to_condition_snow(self):
        """Test weather condition conversion for snow"""
        assert to_condition(15) == "Snowfall"

    def test_to_condition_thunderstorm(self):
        """Test weather condition conversion for thunderstorm"""
        assert to_condition(25) == "Thunderstorm"

    def test_to_condition_storm(self):
        """Test weather condition conversion for storm"""
        assert to_condition(27) == "Storm"

    def test_to_condition_invalid_zero(self):
        """Test weather condition conversion with invalid zero"""
        assert to_condition(0) is None

    def test_to_condition_invalid_none(self):
        """Test weather condition conversion with None"""
        assert to_condition(None) is None

    def test_to_condition_invalid_too_high(self):
        """Test weather condition conversion with out of range value"""
        assert to_condition(28) is None
        assert to_condition(100) is None

    def test_to_condition_invalid_negative(self):
        """Test weather condition conversion with negative value"""
        assert to_condition(-1) is None
