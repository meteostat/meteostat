"""
ERA5-Land grid-cell elevation lookup

Best-effort utility for comparing a coordinate's real elevation against the
elevation ERA5-Land's own 0.1-degree model grid assumes there - useful for
spotting isolated peaks/valleys where a reanalysis grid cell's averaged
terrain diverges sharply from the real, point-scale elevation.

Not called automatically by the hourly provider: resolving it requires
downloading a ~50MB auxiliary file and the optional 'h5py' package, so it
only runs when a caller asks for it directly, or by setting
config.era5_max_elevation_diff (which makes the hourly provider call it and
skip a coordinate whose grid-cell elevation diverges too far from its own).
"""

import os
from typing import Optional

from meteostat.core.cache import cache_service
from meteostat.core.logger import logger
from meteostat.core.network import network_service
from meteostat.api.config import config
from meteostat.providers.era5.hourly import _snap_index

# ERA5-Land's own invariant geopotential field uses a different grid convention
# than the hourly ARCO data: latitude descends 90 -> -90, longitude is 0 -> 359.9
GEOPOTENTIAL_LAT_START = 90.0
GEOPOTENTIAL_LAT_STEP = -0.1
GEOPOTENTIAL_LON_START = 0.0
GEOPOTENTIAL_LON_STEP = 0.1
GEOPOTENTIAL_LAT_SIZE = 1801
GEOPOTENTIAL_LON_SIZE = 3600


def _geopotential_grid_index(lat: float, lon: float) -> tuple[int, int]:
    """
    Resolve a (latitude, longitude) coordinate to the nearest index in
    ERA5-Land's own invariant geopotential grid
    """
    lon = lon % 360
    lat_idx = _snap_index(lat, GEOPOTENTIAL_LAT_START, GEOPOTENTIAL_LAT_STEP)
    lon_idx = _snap_index(lon, GEOPOTENTIAL_LON_START, GEOPOTENTIAL_LON_STEP)
    return (
        min(max(lat_idx, 0), GEOPOTENTIAL_LAT_SIZE - 1),
        min(max(lon_idx, 0), GEOPOTENTIAL_LON_SIZE - 1),
    )


def _get_geopotential_file() -> Optional[str]:
    """
    Download (once) and return the local path to ERA5-Land's own invariant
    geopotential field

    This is a ~50MB NetCDF4 file published as a public ECMWF Confluence
    attachment, already interpolated to ERA5-Land's native 0.1-degree grid -
    unlike the hourly ARCO data, no CDS API key is needed for this one, since
    it's a static auxiliary parameter rather than part of the main archive.
    """
    filepath = config.era5_geopotential_file
    ttl = config.era5_geopotential_ttl

    if os.path.exists(filepath) and not cache_service.is_stale(filepath, ttl):
        return filepath

    try:
        logger.info(
            "Downloading ERA5-Land's invariant geopotential reference data "
            "(~50MB, one-time download)..."
        )
        response = network_service.get(config.era5_geopotential_url, stream=True)

        if response.status_code != 200:
            logger.debug(
                f"Failed to download ERA5-Land geopotential file (status: {response.status_code})"
            )
            return None

        cache_service.create_cache_dir()

        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return filepath

    except Exception as error:
        logger.debug(f"Could not download ERA5-Land geopotential file: {error}")
        return None


# Memoized per (lat_idx, lon_idx): see grid_elevation()
_grid_elevation_cache: dict[tuple[int, int], Optional[float]] = {}


def grid_elevation(latitude: float, longitude: float) -> Optional[float]:
    """
    Best-effort lookup of the elevation ERA5-Land's own model grid assumes at
    this coordinate, for comparison against the real station/point elevation

    Reanalysis grid cells average terrain over a wide area, so an isolated
    peak or valley can end up with a very different "effective" elevation
    than its real one. Returns None (silently) if the 'h5py' extra isn't
    installed, or if the geopotential reference file can't be downloaded.
    """
    key = _geopotential_grid_index(latitude, longitude)

    if key in _grid_elevation_cache:
        return _grid_elevation_cache[key]

    elevation = None
    try:
        import h5py

        filepath = _get_geopotential_file()

        if filepath is not None:
            with h5py.File(filepath, "r") as file:
                geopotential = float(file["z"][0, key[0], key[1]])
                elevation = geopotential / 9.80665  # geopotential -> metres
    except ImportError:
        pass
    except Exception as error:
        logger.debug(f"Could not resolve ERA5-Land grid elevation: {error}")

    _grid_elevation_cache[key] = elevation

    return elevation
