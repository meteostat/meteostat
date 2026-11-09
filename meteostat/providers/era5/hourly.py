"""
Hourly ERA5-Land Reanalysis Data Provider

Get hourly ERA5-Land reanalysis data (0.1-degree resolution) for any
coordinates worldwide, from ECMWF's official Climate Data Store Analysis
Ready Cloud Optimised (ARCO) Zarr archive.

Requires a free Climate Data Store (CDS) personal API key
(https://cds.climate.copernicus.eu, set via config.copernicus_cds_api_key) and,
once per account, accepting the "cc-by" licence on the ERA5-Land dataset
page (https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land).

We talk to the ARCO store with plain HTTP requests and decode raw Zarr v2
chunks ourselves (via numcodecs), rather than depending on
icechunk/xarray/zarr: at the time of writing, going through
xarray.open_zarr()/zarr.open_consolidated() against this store silently
drops the Authorization header partway through its fsspec plumbing,
while plain `requests` calls with the same header work fine.

Despite the name, the "geo-chunked" store variant (not "time-chunked") is
the one suited for point time series: its chunks span ~3.85 years for a
tiny 4x8 grid-cell block, whereas "time-chunked" chunks span a single
hour across a huge area (meant for whole-map snapshots).

The CDS backend has been observed to intermittently return a transient
403 ("LICENSES_NOT_ACCEPTED") even for an already-licensed, already-working
key/endpoint combination; requests are retried a few times to absorb this.

License: CC BY 4.0 - Copernicus Climate Change Service (C3S) / ECMWF
"""

import math
from datetime import datetime, timedelta
from time import sleep
from typing import Optional

import numpy as np
import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.core.cache import cache_service
from meteostat.core.network import network_service
from meteostat.api.config import config
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import (
    kelvin_to_celsius,
    ms_to_kmh,
    temp_dwpt_to_rhum,
)

EPOCH = datetime(1970, 1, 1)

# The ARCO grid: 0.1-degree global, starting at (-90, -179.9)
GRID_LAT_START = -90.0
GRID_LON_START = -179.9
GRID_STEP = 0.1
GRID_LAT_SIZE = 1801
GRID_LON_SIZE = 3600


def _snap_index(value: float, start: float, step: float) -> int:
    """
    Resolve a coordinate to its nearest grid index along a regularly-spaced
    axis, breaking an exact tie (a coordinate sitting precisely on a
    half-grid-point, e.g. a latitude ending in .05 on this 0.1-degree grid)
    toward the higher coordinate value - matching how other ERA5-Land
    consumers (verified against Open-Meteo's archive API) resolve the same
    case. Python's builtin round() instead uses banker's rounding, which
    picks the lower or higher neighboring cell arbitrarily depending on the
    resulting index's parity, silently reading data up to a full grid cell
    (~11km) away from the intended point.

    The 1e-9 nudge below matters: (value - start) / step lands on an exact
    *.5 mathematically for a tie, but floating-point subtraction can put it
    a few ULPs on either side (e.g. (8.45 - -179.9) / 0.1 == 1883.4999999999998,
    not 1883.5 - found via a real cross-check against independent ERA5-Land extraction for a
    Kleiner Feldberg request, where this silently read the grid cell 0.1
    degrees west of the intended one). Real station/point coordinates are
    never specified to anywhere near 1e-9-degree precision, so the nudge
    can't flip a genuine (non-tied) coordinate to the wrong cell.
    """
    idx_float = (value - start) / step
    return (
        math.floor(idx_float + 0.5 + 1e-9)
        if step > 0
        else math.ceil(idx_float - 0.5 - 1e-9)
    )


# "geo-chunked" stores are chunked (time, lat, lon) with a huge time span
# and a tiny spatial block - ideal for point time series
CHUNK_TIME_SIZE = 33792
CHUNK_LAT_SIZE = 4
CHUNK_LON_SIZE = 8

# Raw ERA5-Land variable -> (ARCO store group, S3 bucket id for that group)
#
# "sp" (surface pressure) is intentionally not mapped to Meteostat's PRES, which is
# defined as MSL pressure: reducing a model's surface pressure to MSL requires the
# model's own grid-cell elevation (not the real station elevation), since a 0.1-degree
# grid cell still smooths mountainous terrain. ERA5-Land's ARCO product doesn't expose
# that grid-cell elevation, and using the real station elevation instead was verified
# to produce a systematically biased-high MSL pressure (~30 hPa off on a cross-check
# against real station data), so pressure is left unsupported here rather than wrong.
RAW_VAR_GROUP: dict[str, tuple[str, str]] = {
    "t2m": ("sfc-2m-temperature", "cadl-arco-geo-007"),
    "d2m": ("sfc-2m-temperature", "cadl-arco-geo-007"),
    "tp": ("sfc-pressure-precipitation", "cadl-arco-geo-009"),
    "u10": ("sfc-wind", "cadl-arco-geo-008"),
    "v10": ("sfc-wind", "cadl-arco-geo-008"),
    "sf": ("sfc-snow", "cadl-arco-geo-030"),
    "sde": ("sfc-snow", "cadl-arco-geo-030"),
}

# Which raw ERA5-Land variables need to be fetched to compute a given Meteostat parameter
PARAMETER_DEPENDENCIES: dict[Parameter, tuple[str, ...]] = {
    Parameter.TEMP: ("t2m",),
    Parameter.DWPT: ("d2m",),
    Parameter.RHUM: ("t2m", "d2m"),
    Parameter.PRCP: ("tp",),
    Parameter.SNOW: ("sf",),
    Parameter.SNWD: ("sde",),
    Parameter.WDIR: ("u10", "v10"),
    Parameter.WSPD: ("u10", "v10"),
}

# Raw ERA5-Land variable -> Meteostat parameter (1:1, same physical quantity)
RAW_TO_PARAMETER: dict[str, Parameter] = {
    "t2m": Parameter.TEMP,
    "d2m": Parameter.DWPT,
    "tp": Parameter.PRCP,
    "sf": Parameter.SNOW,
    "sde": Parameter.SNWD,
}


# Memoized per (group, bucket): see _get_time_origin()
_time_origin_cache: dict[tuple[str, str], int] = {}


def _get_time_origin(group: str, bucket: str) -> Optional[int]:
    """
    Resolve the "hours since 1970-01-01" value stored at index 0 of this
    store's time axis

    The time axis is a contiguous hourly sequence, but its array index 0
    does NOT correspond to the 1970-01-01 epoch used in its own "hours
    since 1970-01-01" units attribute - the dataset actually starts around
    1950, so index 0 holds a large *negative* value. Array indices must be
    computed relative to this origin, not against the epoch directly.
    """
    key = (group, bucket)

    if key not in _time_origin_cache:
        try:
            import numcodecs
        except ImportError:
            return None

        url = (
            f"{config.era5_endpoint}/{bucket}/arco/reanalysis_era5_land/"
            f"{group}/geoChunked.zarr/time/0"
        )
        raw = _get_chunk(url)

        if raw is None:
            return None

        try:
            decompressed = numcodecs.blosc.decompress(raw)
            values = np.frombuffer(decompressed, dtype="<i8")
            _time_origin_cache[key] = int(values[0])
        except Exception as error:
            logger.error(error, exc_info=True)
            return None

    return _time_origin_cache[key]


def _get_chunk(url: str) -> Optional[bytes]:
    """
    Fetch a single Zarr chunk, retrying a few times on the CDS backend's
    intermittent "LICENSES_NOT_ACCEPTED" 403 (seen even for an already
    licensed, otherwise working key)
    """
    headers = {"Authorization": f"Bearer {config.copernicus_cds_api_key}"}

    for attempt in range(5):
        response = network_service.get(url, headers=headers)

        if response.status_code == 200:
            return response.content

        if response.status_code == 403 and "LICENSES_NOT_ACCEPTED" in response.text:
            sleep(0.5)
            continue

        logger.warning(
            f"Failed to fetch ERA5 chunk '{url}' (status: {response.status_code})"
        )
        return None

    logger.warning(f"ERA5 chunk '{url}' kept failing with LICENSES_NOT_ACCEPTED")
    return None


@cache_service.cache(TTL.MONTH, "pickle")
def get_chunk_series(
    raw_var: str,
    lat_chunk_idx: int,
    lon_chunk_idx: int,
    lat_within: int,
    lon_within: int,
    time_chunk_idx: int,
) -> Optional[pd.DataFrame]:
    """
    Fetch and decode one Zarr chunk, returning the full chunk's hourly time
    series for a single grid cell and variable

    Cached per chunk (each covering ~3.85 years for this grid cell), so a
    query for a sub-range of an already-fetched chunk is served entirely
    from the local cache.
    """
    try:
        import numcodecs
    except ImportError:
        logger.warning(
            "The ERA5 provider requires the 'numcodecs' package. "
            "Install the 'extras' dependency group to use this provider."
        )
        return None

    group, bucket = RAW_VAR_GROUP[raw_var]

    origin = _get_time_origin(group, bucket)

    if origin is None:
        return None

    url = (
        f"{config.era5_endpoint}/{bucket}/arco/reanalysis_era5_land/"
        f"{group}/geoChunked.zarr/{raw_var}/{time_chunk_idx}.{lat_chunk_idx}.{lon_chunk_idx}"
    )

    raw = _get_chunk(url)

    if raw is None:
        return None

    try:
        decompressed = numcodecs.blosc.decompress(raw)
        values = np.frombuffer(decompressed, dtype="<f4")
        time_len = values.size // (CHUNK_LAT_SIZE * CHUNK_LON_SIZE)
        values = values.reshape((time_len, CHUNK_LAT_SIZE, CHUNK_LON_SIZE))
        series = values[:, lat_within, lon_within]

        chunk_start = EPOCH + timedelta(hours=origin + time_chunk_idx * CHUNK_TIME_SIZE)
        index = pd.date_range(
            start=chunk_start, periods=time_len, freq="h", name="time"
        )

        return pd.DataFrame({raw_var: series}, index=index)

    except Exception as error:
        logger.error(error, exc_info=True)
        return None


def _grid_index(lat: float, lon: float) -> tuple[int, int]:
    """
    Resolve a (latitude, longitude) coordinate to the nearest ARCO grid index
    """
    lon = ((lon + 180) % 360) - 180  # normalize to [-180, 180)
    lat_idx = _snap_index(lat, GRID_LAT_START, GRID_STEP)
    lon_idx = _snap_index(lon, GRID_LON_START, GRID_STEP)
    return (
        min(max(lat_idx, 0), GRID_LAT_SIZE - 1),
        min(max(lon_idx, 0), GRID_LON_SIZE - 1),
    )


def get_series(
    latitude: float,
    longitude: float,
    raw_var: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> Optional[pd.DataFrame]:
    """
    Assemble a raw ERA5-Land variable's time series for a coordinate and date range
    from the per-chunk cache
    """
    lat_idx, lon_idx = _grid_index(latitude, longitude)
    lat_chunk_idx, lat_within = divmod(lat_idx, CHUNK_LAT_SIZE)
    lon_chunk_idx, lon_within = divmod(lon_idx, CHUNK_LON_SIZE)

    group, bucket = RAW_VAR_GROUP[raw_var]
    origin = _get_time_origin(group, bucket)

    if origin is None:
        return None

    # Array indices are relative to the time axis's own origin, not the 1970-01-01
    # epoch used in its units attribute (see _get_time_origin); clip below zero in
    # case the requested range starts before the dataset's actual beginning
    start_hour = max(0, int((start - EPOCH).total_seconds() // 3600) - origin)
    end_hour = max(0, int((end - EPOCH).total_seconds() // 3600) - origin)
    start_chunk = start_hour // CHUNK_TIME_SIZE
    end_chunk = end_hour // CHUNK_TIME_SIZE

    frames = [
        chunk_df
        for time_chunk_idx in range(start_chunk, end_chunk + 1)
        if (
            chunk_df := get_chunk_series(
                raw_var,
                lat_chunk_idx,
                lon_chunk_idx,
                lat_within,
                lon_within,
                time_chunk_idx,
            )
        )
        is not None
    ]

    if not frames:
        return None

    return pd.concat(frames).loc[start:end]


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    """
    Fetch hourly ERA5-Land reanalysis data for a station's or point's coordinates
    """
    if req.station.latitude is None or req.station.longitude is None:
        return None

    if not config.copernicus_cds_api_key:
        logger.warning(
            "ERA5 requires a free Climate Data Store API key. Please use "
            "config.copernicus_cds_api_key to specify your key. For now, this provider is skipped."
        )
        return None

    raw_vars = sorted(
        {
            var
            for param in req.parameters
            for var in PARAMETER_DEPENDENCIES.get(param, ())
        }
    )

    if not raw_vars:
        logger.info("No mappable parameters for ERA5 hourly data")
        return None

    start = pd.Timestamp(req.start or pd.Timestamp(1950, 1, 1))
    end = pd.Timestamp(req.end or pd.Timestamp.now())

    frames = [
        series
        for raw_var in raw_vars
        if (
            series := get_series(
                req.station.latitude, req.station.longitude, raw_var, start, end
            )
        )
        is not None
    ]

    if not frames:
        return None

    df = pd.concat(frames, axis=1)

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

    if Parameter.PRCP in df.columns:
        df[Parameter.PRCP] = df[Parameter.PRCP] * 1000  # m -> mm

    if Parameter.SNOW in df.columns:
        df[Parameter.SNOW] = df[Parameter.SNOW] * 1000  # m w.e. -> cm snow

    if Parameter.SNWD in df.columns:
        df[Parameter.SNWD] = df[Parameter.SNWD] * 100  # m (actual depth) -> cm

    for column in df.select_dtypes(include="number").columns:
        df[column] = df[column].round(1)

    if df.empty:
        return None

    return df
