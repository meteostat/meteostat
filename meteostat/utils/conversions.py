"""
Functions for converting between different
meteorological data units.

The code is licensed under the MIT license.
"""

import math
from typing import Optional

import pandas as pd

from meteostat.core.logger import logger
from meteostat.enumerations import Parameter, Unit, UnitSystem


def celsius_to_fahrenheit(value: int | float | None) -> Optional[float]:
    """
    Convert Celsius to Fahrenheit
    """
    if value is None or pd.isna(value):
        return None
    return round((value * 9 / 5) + 32, 1)


def celsius_to_kelvin(value: int | float | None) -> Optional[float]:
    """
    Convert Celsius to Kelvin.

    Returns the exact conversion without rounding.
    """
    if value is None or pd.isna(value):
        return None
    return value + 273.15


def millimeters_to_inches(value: int | float | None) -> Optional[float]:
    """
    Convert millimeters to inches
    """
    if value is None or pd.isna(value):
        return None
    return round(value / 25.4, 3)


def centimeters_to_inches(value: int | float | None) -> Optional[float]:
    """
    Convert centimeters to inches
    """
    if value is None or pd.isna(value):
        return None
    return round(value / 2.54, 3)


def meters_to_feet(value: int | float | None) -> Optional[float]:
    """
    Convert meters to feet
    """
    if value is None or pd.isna(value):
        return None
    return round(value / 0.3048, 1)


def kmh_to_ms(value: int | float | None) -> Optional[float]:
    """
    Convert kilometers per hour to meters per second
    """
    if value is None or pd.isna(value):
        return None
    return round(value / 3.6, 1)


def kmh_to_mph(value: int | float | None) -> Optional[float]:
    """
    Convert kilometers per hour to miles per hour
    """
    if value is None or pd.isna(value):
        return None
    return round(value * 0.621371, 1)


def kelvin_to_celsius(value: int | float | None) -> Optional[float]:
    """
    Convert Kelvin to Celsius
    """
    if value is None or pd.isna(value):
        return None
    return float(value) - 273.15


def ms_to_kmh(value: int | float | None) -> Optional[float]:
    """
    Convert m/s to km/h
    """
    if value is None or pd.isna(value):
        return None
    return float(value) * 3.6


def hours_to_minutes(value: int | float | None) -> Optional[float]:
    """
    Convert duration from hours to minutes
    """
    if value is None or pd.isna(value):
        return None
    return float(value) * 60


def temp_dwpt_to_rhum(
    row: pd.Series | dict[str, int | float | None],
) -> Optional[float]:
    """
    Get relative humidity from temperature and dew point
    """
    temp = row["temp"]
    dew_point = row["dwpt"]

    if (
        temp is None
        or dew_point is None
        or pd.isna(temp)
        or pd.isna(dew_point)
        or not isinstance(temp, (int, float))
        or not isinstance(dew_point, (int, float))
    ):
        return None

    return 100 * (
        math.exp((17.625 * dew_point) / (243.04 + dew_point))
        / math.exp((17.625 * temp) / (243.04 + temp))
    )


def pres_to_msl(
    row: pd.Series | dict[str, object],
    altitude: Optional[int] = None,
    temp: str = Parameter.TEMP,
) -> Optional[float]:
    pres = row.get(Parameter.PRES)
    t = row.get(temp)

    if pd.isna(pres) or pd.isna(t) or altitude is None:
        return None

    # Type narrowing for arithmetic operations
    if not isinstance(pres, (int, float)) or not isinstance(t, (int, float)):
        return None

    # Check for invalid pressure values
    if pres < 0:
        return None

    try:
        return round(
            pres
            * math.pow(
                1 - (0.0065 * altitude) / (t + 0.0065 * altitude + 273.15),
                -5.257,
            ),
            1,
        )
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.debug("pres_to_msl calculation failed: %s", e)
        return None


def percentage_to_okta(value: int | float | None) -> Optional[int]:
    """
    Convert cloud cover percentage to oktas
    """
    if value is None or pd.isna(value):
        return None
    return round(float(value) / 12.5)


def jcm2_to_wm2(value: int | float | None) -> Optional[int]:
    """
    Convert Joule/CM^2 to Watt/M^2
    """
    if value is None or pd.isna(value):
        return None
    return round(float(value) * 2.78)


def to_direction(value: int | float | None) -> Optional[str]:
    """
    Convert degrees to wind direction
    """
    # Handle None and NaN values
    if value is None or pd.isna(value):
        return None

    # Normalize value to 0-359 range
    value = value % 360

    wdir = None

    if (337 <= value <= 360) or value <= 23:
        wdir = "N"
    if 24 <= value <= 68:
        wdir = "NE"
    if 69 <= value <= 113:
        wdir = "E"
    if 114 <= value <= 158:
        wdir = "SE"
    if 159 <= value <= 203:
        wdir = "S"
    if 204 <= value <= 248:
        wdir = "SW"
    if 249 <= value <= 293:
        wdir = "W"
    if 294 <= value <= 336:
        wdir = "NW"

    return wdir


def to_condition(value: int | float | None) -> Optional[str]:
    """
    Convert Meteostat condition code to descriptive string
    """
    # Handle None and NaN values
    if value is None or pd.isna(value):
        return None

    if value < 1 or value > 27:
        return None

    return [
        "Clear",
        "Fair",
        "Cloudy",
        "Overcast",
        "Fog",
        "Freezing Fog",
        "Light Rain",
        "Rain",
        "Heavy Rain",
        "Freezing Rain",
        "Heavy Freezing Rain",
        "Sleet",
        "Heavy Sleet",
        "Light Snowfall",
        "Snowfall",
        "Heavy Snowfall",
        "Rain Shower",
        "Heavy Rain Shower",
        "Sleet Shower",
        "Heavy Sleet Shower",
        "Snow Shower",
        "Heavy Snow Shower",
        "Lightning",
        "Hail",
        "Thunderstorm",
        "Heavy Thunderstorm",
        "Storm",
    ][int(value) - 1]


CONVERSION_MAPPINGS = {
    Unit.CELSIUS: {
        UnitSystem.IMPERIAL: celsius_to_fahrenheit,
        UnitSystem.SI: celsius_to_kelvin,
    },
    Unit.MILLIMETERS: {
        UnitSystem.IMPERIAL: millimeters_to_inches,
    },
    Unit.CENTIMETERS: {
        UnitSystem.IMPERIAL: centimeters_to_inches,
    },
    Unit.KMH: {
        UnitSystem.SI: kmh_to_ms,
        UnitSystem.IMPERIAL: kmh_to_mph,
    },
    Unit.METERS: {
        UnitSystem.IMPERIAL: meters_to_feet,
    },
}
