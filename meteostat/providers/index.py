"""
Provider Index

This module contains a list of all available data providers.
"""

from datetime import date, timedelta

from meteostat.typing import License, ProviderSpec
from meteostat.enumerations import Grade, Granularity, Parameter, Provider, Priority

PROVIDER_HOURLY = ProviderSpec(
    id=Provider.HOURLY,
    name="Meteostat Hourly",
    granularity=Granularity.HOURLY,
    priority=Priority.NONE,
    grade=None,
    license=None,
    requires=["id"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.SNWD,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.CLDC,
        Parameter.COCO,
    ],
    start=date(1931, 1, 1),
    module="meteostat.providers.meteostat.hourly",
)

PROVIDER_DAILY = ProviderSpec(
    id=Provider.DAILY,
    name="Meteostat Daily",
    granularity=Granularity.DAILY,
    priority=Priority.NONE,
    grade=None,
    license=None,
    requires=["id"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.SNWD,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.CLDC,
    ],
    start=date(1899, 1, 1),
    module="meteostat.providers.meteostat.daily",
)

PROVIDER_DAILY_DERIVED = ProviderSpec(
    id=Provider.DAILY_DERIVED,
    name="Meteostat Daily Derived",
    granularity=Granularity.DAILY,
    priority=Priority.NONE,
    grade=None,
    license=None,
    requires=["id"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.SNOW,
        Parameter.WSPD,
        Parameter.WDIR,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.CLDC,
    ],
    start=date(1931, 1, 1),
    module="meteostat.providers.meteostat.daily_derived",
)

PROVIDER_MONTHLY = ProviderSpec(
    id=Provider.MONTHLY,
    name="Meteostat Monthly",
    granularity=Granularity.MONTHLY,
    priority=Priority.NONE,
    grade=None,
    license=None,
    requires=["id"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.PRES,
        Parameter.TSUN,
    ],
    start=date(1899, 1, 1),
    module="meteostat.providers.meteostat.monthly",
)

PROVIDER_MONTHLY_DERIVED = ProviderSpec(
    id=Provider.MONTHLY_DERIVED,
    name="Meteostat Monthly Derived",
    granularity=Granularity.MONTHLY,
    priority=Priority.NONE,
    grade=None,
    license=None,
    requires=["id"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.PRES,
        Parameter.TSUN,
    ],
    start=date(1899, 1, 1),
    module="meteostat.providers.meteostat.monthly_derived",
)

PROVIDER_DWD_HOURLY = ProviderSpec(
    id=Provider.DWD_HOURLY,
    name="DWD Hourly",
    granularity=Granularity.HOURLY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    countries=["DE"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.VSBY,
        Parameter.COCO,
    ],
    start=date(1939, 1, 1),
    module="meteostat.providers.dwd.hourly",
)

PROVIDER_DWD_POI = ProviderSpec(
    id=Provider.DWD_POI,
    name="DWD POI",
    granularity=Granularity.HOURLY,
    priority=Priority.MEDIUM,
    grade=Grade.OBSERVATION,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    parameters=[
        Parameter.CLDC,
        Parameter.TEMP,
        Parameter.VSBY,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRCP,
        Parameter.RHUM,
        Parameter.WDIR,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.COCO,
        Parameter.SNWD,
    ],
    start=date.today() - timedelta(days=1),
    module="meteostat.providers.dwd.poi",
)

PROVIDER_DWD_MOSMIX = ProviderSpec(
    id=Provider.DWD_MOSMIX,
    name="DWD MOSMIX",
    granularity=Granularity.HOURLY,
    priority=Priority.LOWEST,
    grade=Grade.FORECAST,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.CLDC,
        Parameter.COCO,
    ],
    start=date.today(),
    module="meteostat.providers.dwd.mosmix",
)

PROVIDER_DWD_DAILY = ProviderSpec(
    id=Provider.DWD_DAILY,
    name="DWD Daily",
    granularity=Granularity.DAILY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    countries=["DE"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.SNWD,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.TSUN,
        Parameter.CLDC,
    ],
    start=date(1781, 1, 1),
    module="meteostat.providers.dwd.daily",
)

PROVIDER_DWD_MONTHLY = ProviderSpec(
    id=Provider.DWD_MONTHLY,
    name="DWD Monthly",
    granularity=Granularity.MONTHLY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    countries=["DE"],
    parameters=[Parameter.TEMP, Parameter.TMIN, Parameter.TMAX, Parameter.PRCP],
    start=date(1851, 1, 1),
    module="meteostat.providers.dwd.monthly",
)

PROVIDER_ECCC_HOURLY = ProviderSpec(
    id=Provider.ECCC_HOURLY,
    name="ECCC Hourly",
    granularity=Granularity.HOURLY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Environment and Climate Change Canada",
        name="Environment and Climate Change Canada Data Servers End-use Licence",
        url="https://eccc-msc.github.io/open-data/licence/readme_en/",
    ),
    requires=["identifiers"],
    countries=["CA"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.VSBY,
    ],
    start=date(1939, 1, 1),
    module="meteostat.providers.eccc.hourly",
)

PROVIDER_ECCC_DAILY = ProviderSpec(
    id=Provider.ECCC_DAILY,
    name="ECCC Daily",
    granularity=Granularity.DAILY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Environment and Climate Change Canada",
        name="Environment and Climate Change Canada Data Servers End-use Licence",
        url="https://eccc-msc.github.io/open-data/licence/readme_en/",
    ),
    requires=["identifiers"],
    countries=["CA"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.SNOW,
        Parameter.SNWD,
        Parameter.WPGT,
    ],
    start=date(1939, 1, 1),
    module="meteostat.providers.eccc.daily",
)

PROVIDER_ECCC_MONTHLY = ProviderSpec(
    id=Provider.ECCC_MONTHLY,
    name="ECCC Monthly",
    granularity=Granularity.MONTHLY,
    priority=Priority.HIGHEST,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Environment and Climate Change Canada",
        name="Environment and Climate Change Canada Data Servers End-use Licence",
        url="https://eccc-msc.github.io/open-data/licence/readme_en/",
    ),
    requires=["identifiers"],
    countries=["CA"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.PDAY,
        Parameter.SNOW,
    ],
    start=date(1939, 1, 1),
    module="meteostat.providers.eccc.monthly",
)

PROVIDER_ISD_LITE = ProviderSpec(
    id=Provider.ISD_LITE,
    name="NOAA ISD Lite",
    granularity=Granularity.HOURLY,
    priority=Priority.HIGH,
    grade=Grade.OBSERVATION,
    license=License(
        commercial=True,
        name="CC0 1.0 Universal",
        url="https://creativecommons.org/publicdomain/zero/1.0/",
    ),  # source: https://registry.opendata.aws/noaa-isd/
    requires=["identifiers"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.CLDC,
    ],
    start=date(1931, 1, 1),
    module="meteostat.providers.noaa.isd_lite",
)

PROVIDER_GHCND = ProviderSpec(
    id=Provider.GHCND,
    name="NOAA GHCN-Daily",
    granularity=Granularity.DAILY,
    priority=Priority.HIGH,
    grade=Grade.OBSERVATION,
    license=License(
        commercial=True,
        name="CC0 1.0 Universal",
        url="https://creativecommons.org/publicdomain/zero/1.0/",
    ),  # source: https://registry.opendata.aws/noaa-ghcn/
    requires=["identifiers"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.PRCP,
        Parameter.SNOW,
        Parameter.WSPD,
        Parameter.WDIR,
        Parameter.WPGT,
        Parameter.TSUN,
        Parameter.CLDC,
    ],
    start=date(1931, 1, 1),
    module="meteostat.providers.noaa.ghcnd",
)

PROVIDER_CLIMAT = ProviderSpec(
    id=Provider.CLIMAT,
    name="DWD CLIMAT",
    granularity=Granularity.MONTHLY,
    priority=Priority.HIGH,
    grade=Grade.RECORD,
    license=License(
        commercial=True,
        attribution="Deutscher Wetterdienst",
        name="CC BY 4.0",
        url="https://creativecommons.org/licenses/by/4.0/",
    ),
    requires=["identifiers"],
    parameters=[
        Parameter.TEMP,
        Parameter.TMIN,
        Parameter.TMAX,
        Parameter.TXMN,
        Parameter.TXMX,
        Parameter.PRES,
        Parameter.PRCP,
        Parameter.TSUN,
    ],
    start=date(1875, 6, 1),
    module="meteostat.providers.dwd.climat",
)

PROVIDER_METAR = ProviderSpec(
    id=Provider.METAR,
    name="METAR",
    granularity=Granularity.HOURLY,
    priority=Priority.LOW,
    grade=Grade.OBSERVATION,
    license=License(
        commercial=True,
    ),
    requires=["identifiers"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.PRES,
        Parameter.COCO,
    ],
    start=date.today() - timedelta(days=1),
    module="meteostat.providers.noaa.metar",
)

PROVIDER_METNO_FORECAST = ProviderSpec(
    id=Provider.METNO_FORECAST,
    name="MET Norway Forecast",
    granularity=Granularity.HOURLY,
    priority=Priority.LOWEST - 1,  # MOSMIX is more specific, therefore higher prio
    grade=Grade.FORECAST,
    license=License(
        commercial=True,
        attribution="MET Norway",
        name="NLOD 2.0",
        url="https://data.norge.no/nlod/en/2.0",
    ),
    requires=["location"],
    parameters=[
        Parameter.TEMP,
        Parameter.RHUM,
        Parameter.PRCP,
        Parameter.WDIR,
        Parameter.WSPD,
        Parameter.WPGT,
        Parameter.PRES,
        Parameter.CLDC,
        Parameter.COCO,
    ],
    start=date.today(),
    module="meteostat.providers.metno.forecast",
)


DEFAULT_PROVIDERS = [
    PROVIDER_HOURLY,
    PROVIDER_DAILY,
    PROVIDER_DAILY_DERIVED,
    PROVIDER_MONTHLY,
    PROVIDER_MONTHLY_DERIVED,
    PROVIDER_DWD_HOURLY,
    PROVIDER_DWD_POI,
    PROVIDER_DWD_MOSMIX,
    PROVIDER_DWD_DAILY,
    PROVIDER_DWD_MONTHLY,
    PROVIDER_ECCC_HOURLY,
    PROVIDER_ECCC_DAILY,
    PROVIDER_ECCC_MONTHLY,
    PROVIDER_ISD_LITE,
    PROVIDER_GHCND,
    PROVIDER_CLIMAT,
    PROVIDER_METAR,
    PROVIDER_METNO_FORECAST,
]
