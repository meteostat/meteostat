"""
Meteostat Enumerations
"""

from enum import StrEnum, IntEnum


class Granularity(StrEnum):
    """
    The different levels of time series granularity
    """

    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"
    NORMALS = "normals"


class Frequency(StrEnum):
    """
    The different levels of time series frequency
    """

    HOURLY = "h"
    DAILY = "D"
    MONTHLY = "MS"


class Parameter(StrEnum):
    """
    The different meteorological parameters supported by Meteostat
    """

    TEMP = "temp"  # Air temperature (aggregation: mean)
    TMIN = "tmin"  # Daily minimum air temperature (aggregation: mean)
    TMAX = "tmax"  # Daily maximum air temperature (aggregation: mean)
    TXMN = "txmn"  # Extreme minimum air temperature (aggregation: min)
    TXMX = "txmx"  # Extreme maximum air temperature (aggregation: max)
    DWPT = "dwpt"  # Dew point (aggregation: mean)
    PRCP = "prcp"  # Precipitation (aggregation: sum)
    PDAY = "pday"  # Days with precipitation equal to or greater than 1 millimeter (aggregation: sum)
    WDIR = "wdir"  # Wind direction at observation time
    WSPD = "wspd"  # Wind speed (aggregation: mean)
    WPGT = "wpgt"  # Peak wind gust (aggregation: max)
    RHUM = "rhum"  # Relative humidity (aggregation: mean)
    PRES = "pres"  # Air pressure at MSL (aggregation: mean)
    SNWD = "snwd"  # Snow depth on ground
    SNOW = "snow"  # Snowfall (aggregation: sum)
    TSUN = "tsun"  # Sunshine duration (aggregation: sum)
    SGHI = "sghi"  # TBD
    SDNI = "sdni"  # TBD
    SDHI = "sdhi"  # TBD
    CLDC = "cldc"  # Cloud cover (aggregation: mean)
    VSBY = "vsby"  # Visibility (aggregation: mean)
    COCO = "coco"  # Weather condition code at time of observation


class Unit(StrEnum):
    """
    Data Units
    """

    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    KELVIN = "K"
    PERCENTAGE = "%"
    HPA = "hPa"
    MILLIMETERS = "mm"
    CENTIMETERS = "cm"
    METERS = "m"
    KMH = "km/h"
    DEGREES = "°"
    MINUTES = "min"
    OKTAS = "okta"


class UnitSystem(StrEnum):
    """
    Unit Systems
    """

    SI = "si"
    METRIC = "metric"
    IMPERIAL = "imperial"


class Provider(StrEnum):
    """
    Providers supported by Meteostat
    """

    ISD_LITE = "isd_lite"
    METAR = "metar"
    GHCND = "ghcnd"
    CLIMAT = "climat"
    DWD_HOURLY = "dwd_hourly"
    DWD_POI = "dwd_poi"
    DWD_MOSMIX = "dwd_mosmix"
    DWD_DAILY = "dwd_daily"
    DWD_MONTHLY = "dwd_monthly"
    ECCC_HOURLY = "eccc_hourly"
    ECCC_DAILY = "eccc_daily"
    ECCC_MONTHLY = "eccc_monthly"
    METNO_FORECAST = "metno_forecast"

    HOURLY = "hourly"
    DAILY = "daily"
    DAILY_DERIVED = "daily_derived"
    MONTHLY = "monthly"
    MONTHLY_DERIVED = "monthly_derived"

    SYNOP = "synop"
    METAR_LEGACY = "metar_legacy"
    MODEL = "model"


class Priority(IntEnum):
    """
    Provider priorities
    """

    HIGHEST = 25
    HIGH = 20
    MEDIUM = 15
    LOW = 10
    LOWEST = 5
    NONE = 0


class Grade(IntEnum):
    """
    Provider quality grades
    """

    RECORD = 4
    OBSERVATION = 3
    ANALYSIS = 2
    FORECAST = 1


class TTL(IntEnum):
    """
    Cache TTLs
    """

    HOUR = 60 * 60
    DAY = 60 * 60 * 24
    WEEK = 60 * 60 * 24 * 7
    MONTH = 60 * 60 * 24 * 30
