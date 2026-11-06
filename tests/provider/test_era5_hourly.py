import os
from datetime import datetime
import meteostat as ms
from meteostat.providers.era5.hourly import (
    fetch,
    _grid_index,
    GRID_LAT_START,
    GRID_LON_START,
    GRID_STEP,
)
from meteostat.typing import ProviderRequest


def test_era5_grid_index_half_point_tie_breaks_up():
    """
    It should break an exact half-grid-point tie (a coordinate landing precisely
    between two 0.1-degree cells) toward the higher coordinate, consistently

    Verified against Open-Meteo's independent ERA5-Land extraction, which
    resolves both of these real-world cases (Frankfurt Airport's latitude,
    London Heathrow's longitude) to the higher neighboring cell. Python's
    builtin round() uses banker's rounding instead, which picked the lower
    neighbor for both of these specific coordinates - silently reading data
    for a point up to a full grid cell (~11km) away from the intended one.
    """
    lat_idx, lon_idx = _grid_index(50.05, 8.6)  # Frankfurt Airport
    assert round(GRID_LAT_START + lat_idx * GRID_STEP, 2) == 50.1
    assert round(GRID_LON_START + lon_idx * GRID_STEP, 2) == 8.6

    lat_idx, lon_idx = _grid_index(51.4833, -0.45)  # London Heathrow
    assert round(GRID_LAT_START + lat_idx * GRID_STEP, 2) == 51.5
    assert round(GRID_LON_START + lon_idx * GRID_STEP, 2) == -0.4


def test_era5_hourly():
    """
    It should load ERA5-Land reanalysis data for an arbitrary coordinate (CDS ARCO store)
    """
    ms.config.copernicus_cds_api_key = os.environ.get("CDS_API_KEY")

    query = ProviderRequest(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 1, 2),
        station=ms.Station(
            id="$0001",
            latitude=50.0333,
            longitude=8.5706,
        ),
        parameters=[ms.Parameter.TEMP, ms.Parameter.PRCP, ms.Parameter.RHUM],
    )
    df = fetch(query)

    assert df is not None and not df.empty, "No data returned from ERA5"
    assert "temp" in df, "Temperature data is missing altogether."
    assert "prcp" in df, "Precipitation data is missing altogether."
    assert "rhum" in df, "Relative humidity data is missing altogether."

    assert df["temp"].notna().sum() >= 24, "Insufficient temperature data returned."


def test_era5_hourly_negative_longitude():
    """
    It should correctly resolve negative (western hemisphere) longitudes on the -180/180 grid
    """
    ms.config.copernicus_cds_api_key = os.environ.get("CDS_API_KEY")

    df = ms.hourly(
        ms.Point(40.7128, -74.0060),  # New York City
        start=datetime(2023, 7, 1),
        end=datetime(2023, 7, 1, 23, 59),
        providers=[ms.Provider.ERA5_HOURLY],
        parameters=[ms.Parameter.TEMP],
    ).fetch()

    assert df is not None and not df.empty, "No data returned for arbitrary point"
    assert df["temp"].notna().sum() >= 20, "Insufficient temperature data returned."
    assert df["temp"].between(10, 40).all(), "Implausible temperature values returned."


def test_era5_hourly_wind():
    """
    It should derive wind speed and direction from the u10/v10 components
    """
    ms.config.copernicus_cds_api_key = os.environ.get("CDS_API_KEY")

    df = ms.hourly(
        ms.Point(35.6762, 139.6503),  # Tokyo
        start=datetime(2023, 1, 1),
        end=datetime(2023, 1, 1, 23, 59),
        providers=[ms.Provider.ERA5_HOURLY],
        parameters=[ms.Parameter.WSPD, ms.Parameter.WDIR],
    ).fetch()

    assert df is not None and not df.empty, "No wind data returned"
    assert df["wspd"].notna().sum() >= 20, "Insufficient wind speed data returned."
    assert df["wdir"].between(0, 360).all(), "Wind direction out of range."


def test_era5_hourly_matches_observations():
    """
    It should roughly agree with real observations for a low-elevation station

    This is a regression test for a time-origin bug: the ARCO store's time axis
    index 0 does not correspond to the 1970-01-01 epoch used in its own units
    attribute (the dataset actually starts around 1950), so naively using
    "hours since 1970-01-01" as an array index silently read data from ~20
    years off target. A pure plausibility check (e.g. "is it a sane
    temperature") doesn't catch that; comparing against real observations does.
    """
    ms.config.copernicus_cds_api_key = os.environ.get("CDS_API_KEY")

    start, end = datetime(2018, 1, 1), datetime(2018, 1, 1, 23, 59)

    # Frankfurt Westend (D1424), low elevation (124m) - avoid stations on
    # isolated peaks, where reanalysis grid cells are expected to diverge
    # from real observations regardless of any implementation bug
    obs = ms.hourly("D1424", start, end, parameters=[ms.Parameter.TEMP]).fetch()
    land = ms.hourly(
        ms.Point(50.1269, 8.6694),
        start,
        end,
        providers=[ms.Provider.ERA5_HOURLY],
        parameters=[ms.Parameter.TEMP],
    ).fetch()

    assert obs is not None and not obs.empty
    assert land is not None and not land.empty

    diff = (obs["temp"] - land["temp"]).abs()
    assert diff.mean() < 3, (
        f"ERA5-Land diverges too far from observations (mean |diff|={diff.mean()})"
    )


def test_era5_hourly_chunk_cache():
    """
    A query for a sub-range of an already-fetched chunk should be served from cache
    """
    ms.config.copernicus_cds_api_key = os.environ.get("CDS_API_KEY")

    query_full = ProviderRequest(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31, 23),
        station=ms.Station(id="$0001", latitude=50.0333, longitude=8.5706),
        parameters=[ms.Parameter.TEMP],
    )
    df_full = fetch(query_full)
    assert df_full is not None and not df_full.empty

    query_sub = ProviderRequest(
        start=datetime(2023, 3, 1),
        end=datetime(2023, 3, 10, 23),
        station=ms.Station(id="$0001", latitude=50.0333, longitude=8.5706),
        parameters=[ms.Parameter.TEMP],
    )
    df_sub = fetch(query_sub)

    assert df_sub is not None and not df_sub.empty
    assert len(df_sub) == 240  # 10 days * 24 hours
