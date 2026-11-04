"""
ERA5 hourly data import routine

Get hourly ERA5 reanalysis data for any coordinates worldwide, straight from
Earthmover's Icechunk/Zarr mirror of ERA5 on AWS Open Data (anonymous S3
access, no API key required).

Since ERA5 is a global reanalysis grid rather than a network of stations,
this provider works with any Point/Station coordinates, not just Meteostat's
known weather stations. The nearest 0.25-degree grid cell is used.

Requires the optional "icechunk", "xarray", "zarr" and "numcodecs[pcodec]"
packages (see the "extras" dependency group). The Icechunk v2 store format
used by this dataset requires icechunk>=2.0, which in turn requires
Python >= 3.12; on older Python versions these extras are not installed
and this provider is a no-op.

License: CC BY 4.0 - https://registry.opendata.aws/earthmover-era5/
"""

from typing import Any, Optional

import numpy as np
import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.core.cache import cache_service
from meteostat.api.config import config
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import (
    kelvin_to_celsius,
    ms_to_kmh,
    percentage_to_okta,
    temp_dwpt_to_rhum,
)

# Mapping from raw ERA5 variable names to Meteostat parameters (1:1, same physical quantity)
RAW_TO_PARAMETER: dict[str, Parameter] = {
    "t2m": Parameter.TEMP,
    "d2m": Parameter.DWPT,
    "msl": Parameter.PRES,
    "tp": Parameter.PRCP,
    "sf": Parameter.SNOW,
    "sd": Parameter.SNWD,
    "fg10": Parameter.WPGT,
    "tcc": Parameter.CLDC,
}

# Which raw ERA5 variables need to be fetched to compute a given Meteostat parameter
PARAMETER_DEPENDENCIES: dict[Parameter, tuple[str, ...]] = {
    Parameter.TEMP: ("t2m",),
    Parameter.DWPT: ("d2m",),
    Parameter.RHUM: ("t2m", "d2m"),
    Parameter.PRES: ("msl",),
    Parameter.PRCP: ("tp",),
    Parameter.SNOW: ("sf",),
    Parameter.SNWD: ("sd",),
    Parameter.WDIR: ("u10", "v10"),
    Parameter.WSPD: ("u10", "v10"),
    Parameter.WPGT: ("fg10",),
    Parameter.CLDC: ("tcc",),
}

# In-process cache for the opened Icechunk/Zarr dataset handle (expensive to open)
_dataset_cache: dict[tuple[str, str, str, str], Any] = {}


def _get_dataset() -> Any:
    """
    Open (or reuse an already opened) handle to the Icechunk ERA5 store
    """
    import icechunk
    import xarray as xr

    key = (
        config.era5_bucket,
        config.era5_prefix,
        config.era5_region,
        config.era5_group,
    )

    if key not in _dataset_cache:
        storage = icechunk.s3_storage(
            bucket=config.era5_bucket,
            prefix=config.era5_prefix,
            region=config.era5_region,
            anonymous=True,
        )
        repo = icechunk.Repository.open(storage)
        session = repo.readonly_session("main")
        _dataset_cache[key] = xr.open_zarr(
            session.store, group=config.era5_group, consolidated=False, chunks=None
        )

    return _dataset_cache[key]


@cache_service.cache(TTL.MONTH, "pickle")
def get_year_data(
    latitude: float,
    longitude: float,
    year: int,
    raw_vars: tuple[str, ...],
) -> Optional[pd.DataFrame]:
    """
    Fetch one full calendar year of raw ERA5 variables for the nearest grid cell

    Cached per calendar year, matching the Icechunk store's own chunking
    (one year per chunk). This way, a query for a sub-range of a year that has
    already been fetched is served entirely from the local cache, instead of
    re-fetching from the remote store.
    """
    logger.debug(f"Fetching ERA5 data for ({latitude}, {longitude}) in {year}")

    try:
        ds = _get_dataset()

        # ERA5 longitude runs from 0 to 360 degrees
        subset = ds[list(raw_vars)].sel(
            latitude=latitude, longitude=longitude % 360, method="nearest"
        )
        subset = subset.sel(valid_time=slice(f"{year}-01-01", f"{year}-12-31"))

        df = subset.to_dataframe()[list(raw_vars)]
        df.index = pd.DatetimeIndex(df.index.get_level_values("valid_time"))
        df.index.name = "time"

        return df

    except ImportError:
        logger.warning(
            "The ERA5 provider requires the 'icechunk', 'xarray', 'zarr' and "
            "'numcodecs[pcodec]' packages. Install the 'extras' dependency group "
            "to use this provider."
        )
        return None

    except Exception as error:
        logger.error(error, exc_info=True)
        return None


def get_data(
    latitude: float,
    longitude: float,
    start: pd.Timestamp,
    end: pd.Timestamp,
    raw_vars: tuple[str, ...],
) -> Optional[pd.DataFrame]:
    """
    Assemble the requested date range from per-year cached chunks and derive
    Meteostat parameters from the raw ERA5 variables
    """
    frames = [
        year_df
        for year in range(start.year, end.year + 1)
        if (year_df := get_year_data(latitude, longitude, year, raw_vars)) is not None
    ]

    if not frames:
        return None

    df = pd.concat(frames).loc[start:end]

    if df.empty:
        return None

    if "u10" in df.columns and "v10" in df.columns:
        wspd = np.sqrt(df["u10"] ** 2 + df["v10"] ** 2).apply(ms_to_kmh)
        wdir = (np.degrees(np.arctan2(df["u10"], df["v10"])) + 180) % 360
        df[Parameter.WSPD] = wspd
        df[Parameter.WDIR] = wdir.round().astype("Int64")
        df = df.drop(columns=["u10", "v10"])

    df = df.rename(columns=RAW_TO_PARAMETER)

    if Parameter.TEMP in df.columns:
        df[Parameter.TEMP] = df[Parameter.TEMP].apply(kelvin_to_celsius)

    if Parameter.DWPT in df.columns:
        df[Parameter.DWPT] = df[Parameter.DWPT].apply(kelvin_to_celsius)

    if Parameter.TEMP in df.columns and Parameter.DWPT in df.columns:
        df[Parameter.RHUM] = df.apply(temp_dwpt_to_rhum, axis=1)

    if Parameter.PRES in df.columns:
        df[Parameter.PRES] = df[Parameter.PRES] / 100  # Pa -> hPa

    if Parameter.PRCP in df.columns:
        df[Parameter.PRCP] = df[Parameter.PRCP] * 1000  # m -> mm

    # ERA5 reports "sf"/"sd" as metres of water equivalent; snow depth is
    # roughly 10x the water equivalent depth (fresh snow density assumption)
    if Parameter.SNOW in df.columns:
        df[Parameter.SNOW] = df[Parameter.SNOW] * 1000  # m w.e. -> cm snow

    if Parameter.SNWD in df.columns:
        df[Parameter.SNWD] = df[Parameter.SNWD] * 1000  # m w.e. -> cm snow

    if Parameter.WPGT in df.columns:
        df[Parameter.WPGT] = df[Parameter.WPGT].apply(ms_to_kmh)

    if Parameter.CLDC in df.columns:
        df[Parameter.CLDC] = (df[Parameter.CLDC] * 100).apply(percentage_to_okta)

    for column in df.select_dtypes(include="number").columns:
        df[column] = df[column].round(1)

    return df


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch hourly ERA5 reanalysis data for a station's or point's coordinates
    """
    if req.station.latitude is None or req.station.longitude is None:
        return None

    raw_vars = tuple(
        sorted(
            {
                var
                for param in req.parameters
                for var in PARAMETER_DEPENDENCIES.get(param, ())
            }
        )
    )

    if not raw_vars:
        logger.info("No mappable parameters for ERA5 hourly data")
        return None

    start = pd.Timestamp(req.start or pd.Timestamp(1940, 1, 1))
    end = pd.Timestamp(req.end or pd.Timestamp.now())

    df = get_data(req.station.latitude, req.station.longitude, start, end, raw_vars)

    if df is None or df.empty:
        return None

    return df
