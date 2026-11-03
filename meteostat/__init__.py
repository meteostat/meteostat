"""
█▀▄▀█ █▀▀ ▀█▀ █▀▀ █▀█ █▀ ▀█▀ ▄▀█ ▀█▀
█░▀░█ ██▄ ░█░ ██▄ █▄█ ▄█ ░█░ █▀█ ░█░

A Python library for accessing open weather and climate data.

Meteorological data provided by Meteostat (https://dev.meteostat.net)
under the terms of the Creative Commons Attribution 4.0 International
License.

The code is licensed under the MIT license.
"""

from importlib.metadata import PackageNotFoundError, version

__appname__ = "meteostat"

try:
    __version__ = version("meteostat")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from meteostat.api.daily import daily
from meteostat.api.hourly import hourly
from meteostat.api.interpolate import interpolate
from meteostat.api.inventory import Inventory
from meteostat.api.merge import merge
from meteostat.api.monthly import monthly
from meteostat.api.normals import normals
from meteostat.api.point import Point
from meteostat.api.stations import stations
from meteostat.api.timeseries import TimeSeries
from meteostat.core.cache import purge
from meteostat.api.config import config
from meteostat.enumerations import Granularity, Parameter, Provider, UnitSystem
from meteostat.interpolation.lapserate import lapse_rate
from meteostat.typing import Station, License

# Export public API
__all__ = [
    "config",
    "daily",
    "hourly",
    "Granularity",
    "interpolate",
    "Inventory",
    "lapse_rate",
    "License",
    "merge",
    "monthly",
    "normals",
    "Parameter",
    "Point",
    "Provider",
    "purge",
    "Station",
    "stations",
    "TimeSeries",
    "UnitSystem",
]
