import sys
from datetime import timedelta
from unittest.mock import MagicMock

import numpy as np
import numcodecs
import pandas as pd

import meteostat as ms
from meteostat.providers.era5 import hourly as era5_hourly
from meteostat.providers.era5.hourly import (
    _grid_index,
    GRID_LAT_START,
    GRID_LON_START,
    GRID_STEP,
)
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import kelvin_to_celsius, ms_to_kmh, temp_dwpt_to_rhum


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


def test_era5_grid_index_half_point_tie_breaks_up_despite_float_error():
    """
    Same tie-break rule as above, but for a coordinate where plain
    (value - start) / step lands a few ULPs *below* the exact tie instead
    of exactly on it: (8.45 - -179.9) / 0.1 == 1883.4999999999998 in
    float64, not 1883.5. Caught via a real cross-check against
    independent ERA5-Land extraction for Kleiner Feldberg,
    where this silently read the grid cell 0.1 degrees (~7km) west of the
    intended one.
    """
    lat_idx, lon_idx = _grid_index(50.2167, 8.45)  # Kleiner Feldberg
    assert round(GRID_LAT_START + lat_idx * GRID_STEP, 2) == 50.2
    assert round(GRID_LON_START + lon_idx * GRID_STEP, 2) == 8.5


# ---- _get_chunk ----


def test_get_chunk_returns_content_on_200(mocker):
    mock_network = mocker.patch("meteostat.providers.era5.hourly.network_service")
    mock_network.get.return_value = MagicMock(status_code=200, content=b"chunk-bytes")

    assert era5_hourly._get_chunk("https://example.test/chunk") == b"chunk-bytes"


def test_get_chunk_retries_on_licenses_not_accepted_then_succeeds(mocker):
    mock_network = mocker.patch("meteostat.providers.era5.hourly.network_service")
    mocker.patch("meteostat.providers.era5.hourly.sleep")  # skip the real 0.5s wait

    forbidden = MagicMock(status_code=403, text="LICENSES_NOT_ACCEPTED")
    ok = MagicMock(status_code=200, content=b"ok-bytes")
    mock_network.get.side_effect = [forbidden, ok]

    assert era5_hourly._get_chunk("https://example.test/chunk") == b"ok-bytes"
    assert mock_network.get.call_count == 2


def test_get_chunk_gives_up_after_retries_exhausted(mocker):
    mock_network = mocker.patch("meteostat.providers.era5.hourly.network_service")
    mocker.patch("meteostat.providers.era5.hourly.sleep")

    mock_network.get.return_value = MagicMock(
        status_code=403, text="LICENSES_NOT_ACCEPTED"
    )

    assert era5_hourly._get_chunk("https://example.test/chunk") is None
    assert mock_network.get.call_count == 5


def test_get_chunk_returns_none_on_other_error_status(mocker):
    mock_network = mocker.patch("meteostat.providers.era5.hourly.network_service")
    mock_network.get.return_value = MagicMock(status_code=404, text="Not Found")

    assert era5_hourly._get_chunk("https://example.test/chunk") is None
    assert mock_network.get.call_count == 1


# ---- _get_time_origin ----


def test_get_time_origin_returns_none_without_numcodecs(mocker):
    era5_hourly._time_origin_cache.clear()
    mocker.patch.dict(sys.modules, {"numcodecs": None})

    assert era5_hourly._get_time_origin("group-no-numcodecs", "bucket-x") is None


def test_get_time_origin_returns_none_when_chunk_fetch_fails(mocker):
    era5_hourly._time_origin_cache.clear()
    mocker.patch.object(era5_hourly, "_get_chunk", return_value=None)

    assert era5_hourly._get_time_origin("group-fail", "bucket-fail") is None


def test_get_time_origin_returns_none_on_malformed_payload(mocker):
    era5_hourly._time_origin_cache.clear()
    mocker.patch.object(
        era5_hourly, "_get_chunk", return_value=b"not-a-valid-blosc-payload"
    )

    assert era5_hourly._get_time_origin("group-malformed", "bucket-malformed") is None


def test_get_time_origin_parses_and_caches(mocker):
    era5_hourly._time_origin_cache.clear()
    compressed = numcodecs.blosc.compress(
        np.array([424242], dtype="<i8").tobytes(), b"lz4", 5
    )
    mock_get_chunk = mocker.patch.object(
        era5_hourly, "_get_chunk", return_value=compressed
    )

    assert era5_hourly._get_time_origin("group-cache", "bucket-cache") == 424242
    assert mock_get_chunk.call_count == 1

    # a second call for the same (group, bucket) should be served from the
    # in-process cache rather than fetching the chunk again
    assert era5_hourly._get_time_origin("group-cache", "bucket-cache") == 424242
    assert mock_get_chunk.call_count == 1


# ---- get_chunk_series ----


def test_get_chunk_series_returns_none_without_numcodecs(mocker):
    mocker.patch.dict(sys.modules, {"numcodecs": None})

    assert era5_hourly.get_chunk_series.__wrapped__("t2m", 0, 0, 0, 0, 0) is None


def test_get_chunk_series_returns_none_when_origin_missing(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=None)

    assert era5_hourly.get_chunk_series.__wrapped__("t2m", 0, 0, 0, 0, 0) is None


def test_get_chunk_series_returns_none_when_chunk_fetch_fails(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=0)
    mocker.patch.object(era5_hourly, "_get_chunk", return_value=None)

    assert era5_hourly.get_chunk_series.__wrapped__("t2m", 0, 0, 0, 0, 0) is None


def test_get_chunk_series_returns_none_on_malformed_payload(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=0)
    mocker.patch.object(
        era5_hourly, "_get_chunk", return_value=b"not-a-valid-blosc-payload"
    )

    assert era5_hourly.get_chunk_series.__wrapped__("t2m", 0, 0, 0, 0, 0) is None


def test_get_chunk_series_decodes_real_payload(mocker):
    """
    Build a real blosc-compressed chunk (same layout the ARCO store serves) and
    verify decoding, reshaping and the resulting time index are all correct
    """
    time_len = 2
    values = np.arange(
        era5_hourly.CHUNK_LAT_SIZE * era5_hourly.CHUNK_LON_SIZE * time_len, dtype="<f4"
    ).reshape((time_len, era5_hourly.CHUNK_LAT_SIZE, era5_hourly.CHUNK_LON_SIZE))
    compressed = numcodecs.blosc.compress(values.tobytes(), b"lz4", 5)

    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=100)
    mocker.patch.object(era5_hourly, "_get_chunk", return_value=compressed)

    lat_within, lon_within = 1, 3
    df = era5_hourly.get_chunk_series.__wrapped__(
        "t2m", 0, 0, lat_within, lon_within, 0
    )

    assert df is not None
    assert list(df.columns) == ["t2m"]
    assert df.index[0] == era5_hourly.EPOCH + timedelta(hours=100)
    expected = values[:, lat_within, lon_within].tolist()
    assert df["t2m"].tolist() == expected


# ---- get_series ----


def test_get_series_returns_none_when_origin_missing(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=None)

    result = era5_hourly.get_series(
        50.0, 8.0, "t2m", pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")
    )

    assert result is None


def test_get_series_returns_none_when_all_chunks_missing(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=0)
    mocker.patch.object(era5_hourly, "get_chunk_series", return_value=None)

    result = era5_hourly.get_series(
        50.0, 8.0, "t2m", pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")
    )

    assert result is None


def test_get_series_concatenates_chunks_and_slices_range(mocker):
    mocker.patch.object(era5_hourly, "_get_time_origin", return_value=0)

    hours = pd.date_range("2023-01-01", periods=5, freq="h", name="time")
    chunk_df = pd.DataFrame({"t2m": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=hours)
    mocker.patch.object(era5_hourly, "get_chunk_series", return_value=chunk_df)

    start = pd.Timestamp("2023-01-01 01:00")
    end = pd.Timestamp("2023-01-01 03:00")
    result = era5_hourly.get_series(50.0, 8.0, "t2m", start, end)

    assert result is not None
    assert result["t2m"].tolist() == [2.0, 3.0, 4.0]


# ---- fetch ----


def test_fetch_returns_none_without_coordinates():
    req = ProviderRequest(
        station=ms.Station(id="$0001", latitude=None, longitude=None),
        parameters=[ms.Parameter.TEMP],
        start=pd.Timestamp("2023-01-01"),
        end=pd.Timestamp("2023-01-02"),
    )

    assert era5_hourly.fetch(req) is None


def test_fetch_returns_none_without_api_key():
    original_key = ms.config.copernicus_cds_api_key
    try:
        ms.config.copernicus_cds_api_key = None

        req = ProviderRequest(
            station=ms.Station(id="$0001", latitude=50.0, longitude=8.0),
            parameters=[ms.Parameter.TEMP],
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-02"),
        )

        assert era5_hourly.fetch(req) is None
    finally:
        ms.config.copernicus_cds_api_key = original_key


def test_fetch_returns_none_for_unmappable_parameters():
    original_key = ms.config.copernicus_cds_api_key
    try:
        ms.config.copernicus_cds_api_key = "test-key"

        req = ProviderRequest(
            station=ms.Station(id="$0001", latitude=50.0, longitude=8.0),
            parameters=[ms.Parameter.PRES],  # not in PARAMETER_DEPENDENCIES
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-02"),
        )

        assert era5_hourly.fetch(req) is None
    finally:
        ms.config.copernicus_cds_api_key = original_key


def test_fetch_returns_none_when_no_series_available(mocker):
    original_key = ms.config.copernicus_cds_api_key
    try:
        ms.config.copernicus_cds_api_key = "test-key"
        mocker.patch.object(era5_hourly, "get_series", return_value=None)

        req = ProviderRequest(
            station=ms.Station(id="$0001", latitude=50.0, longitude=8.0),
            parameters=[ms.Parameter.TEMP],
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-02"),
        )

        assert era5_hourly.fetch(req) is None
    finally:
        ms.config.copernicus_cds_api_key = original_key


def test_fetch_happy_path_converts_units_and_derives_wind(mocker):
    """
    Exercise the full post-processing pipeline: wind speed/direction derived
    from u10/v10, Kelvin->Celsius, relative humidity derived from temp/dwpt,
    and the m/m.w.e.->mm/cm unit conversions for prcp/snow/snwd
    """
    original_key = ms.config.copernicus_cds_api_key
    try:
        ms.config.copernicus_cds_api_key = "test-key"

        idx = pd.DatetimeIndex([pd.Timestamp("2023-01-01 00:00")], name="time")
        raw_values = {
            "t2m": 300.0,
            "d2m": 290.0,
            "u10": 3.0,
            "v10": 4.0,
            "tp": 0.002,
            "sf": 0.0005,
            "sde": 0.01,
        }

        def fake_get_series(latitude, longitude, raw_var, start, end):
            return pd.DataFrame({raw_var: [raw_values[raw_var]]}, index=idx)

        mocker.patch.object(era5_hourly, "get_series", side_effect=fake_get_series)

        req = ProviderRequest(
            station=ms.Station(id="$0001", latitude=50.0, longitude=8.0),
            parameters=[
                ms.Parameter.TEMP,
                ms.Parameter.DWPT,
                ms.Parameter.RHUM,
                ms.Parameter.PRCP,
                ms.Parameter.SNOW,
                ms.Parameter.SNWD,
                ms.Parameter.WSPD,
                ms.Parameter.WDIR,
            ],
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-01 23:59"),
        )

        df = era5_hourly.fetch(req)

        assert df is not None
        assert "u10" not in df.columns and "v10" not in df.columns
        row = df.iloc[0]

        # rhum is derived from full-precision Celsius temp/dwpt, *before* the
        # final rounding pass that the temp/dwpt columns themselves go through
        full_temp = kelvin_to_celsius(raw_values["t2m"])
        full_dwpt = kelvin_to_celsius(raw_values["d2m"])
        assert full_temp is not None and full_dwpt is not None
        rhum = temp_dwpt_to_rhum({"temp": full_temp, "dwpt": full_dwpt})
        assert rhum is not None
        expected_rhum = round(rhum, 1)

        expected_temp = round(full_temp, 1)
        expected_dwpt = round(full_dwpt, 1)
        wspd = ms_to_kmh(np.sqrt(raw_values["u10"] ** 2 + raw_values["v10"] ** 2))
        assert wspd is not None
        expected_wspd = round(wspd, 1)
        expected_wdir = round(
            (np.degrees(np.arctan2(raw_values["u10"], raw_values["v10"])) + 180) % 360
        )

        assert row["temp"] == expected_temp
        assert row["dwpt"] == expected_dwpt
        assert row["wspd"] == expected_wspd
        assert row["wdir"] == expected_wdir
        assert row["rhum"] == expected_rhum
        assert row["prcp"] == round(raw_values["tp"] * 1000, 1)
        assert row["snow"] == round(raw_values["sf"] * 1000, 1)
        assert row["snwd"] == round(raw_values["sde"] * 100, 1)
    finally:
        ms.config.copernicus_cds_api_key = original_key


def test_fetch_returns_none_when_resulting_dataframe_is_empty(mocker):
    """
    A raw_var resolving to a series with no rows (e.g. the requested range
    falls entirely outside the grid cell's data) should still yield None,
    not an empty DataFrame
    """
    original_key = ms.config.copernicus_cds_api_key
    try:
        ms.config.copernicus_cds_api_key = "test-key"
        empty_df = pd.DataFrame({"t2m": []}, index=pd.DatetimeIndex([], name="time"))
        mocker.patch.object(era5_hourly, "get_series", return_value=empty_df)

        req = ProviderRequest(
            station=ms.Station(id="$0001", latitude=50.0, longitude=8.0),
            parameters=[ms.Parameter.TEMP],
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-02"),
        )

        assert era5_hourly.fetch(req) is None
    finally:
        ms.config.copernicus_cds_api_key = original_key
