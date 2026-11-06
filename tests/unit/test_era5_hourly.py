from meteostat.providers.era5.hourly import _grid_index, GRID_LAT_START, GRID_LON_START, GRID_STEP


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
