"""
█▀▄▀█ █▀▀ ▀█▀ █▀▀ █▀█ █▀ ▀█▀ ▄▀█ ▀█▀
█░▀░█ ██▄ ░█░ ██▄ █▄█ ▄█ ░█░ █▀█ ░█░

A Python library for accessing open weather and climate data

Meteorological data provided by Meteostat (https://dev.meteostat.net)
under the terms of the Creative Commons Attribution-NonCommercial
4.0 International Public License.

The code is licensed under the MIT license.
"""

__appname__ = "meteostat"
__version__ = "2.0.0"

from meteostat.core.cache import purge
from meteostat.core.config import config
from meteostat.enumerations import Parameter, Provider, UnitSystem
from meteostat.api.stations import stations
from meteostat.api.point import Point
from meteostat.api.hourly import hourly
from meteostat.api.daily import daily
from meteostat.api.monthly import monthly
from meteostat.api.normals import normals
from meteostat.api.merge import merge
from meteostat.api.interpolate import interpolate
from meteostat.interpolation.lapserate import lapse_rate
from meteostat.typing import Station

# Export public API
__all__ = [
    "config",
    "Parameter",
    "purge",
    "Provider",
    "UnitSystem",
    "stations",
    "Point",
    "hourly",
    "daily",
    "monthly",
    "normals",
    "interpolate",
    "merge",
    "lapse_rate",
    "Station",
]
