from datetime import datetime
import pytest
import meteostat as ms
from meteostat.providers.era5.hourly import fetch
from meteostat.typing import ProviderRequest

# The icechunk/zarr/numcodecs[pcodec] stack required to read this dataset's
# Icechunk v2 store only supports Python >= 3.12, so the "extras" dependency
# group is not installable (and these tests are skipped) below that.
pytest.importorskip("icechunk")


def test_era5_hourly():
    """
    It should load ERA5 reanalysis data for an arbitrary coordinate (Earthmover Icechunk mirror)
    """
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
    It should correctly resolve negative (western hemisphere) longitudes on the 0-360 grid
    """
    df = ms.hourly(
        ms.Point(40.7128, -74.0060),  # New York City
        start=datetime(2023, 7, 1),
        end=datetime(2023, 7, 1, 23, 59),
        providers=[ms.Provider.ERA5_HOURLY],
        parameters=[ms.Parameter.TEMP],
    ).fetch()

    assert df is not None and not df.empty, "No data returned for arbitrary point"
    assert df["temp"].notna().sum() >= 20, "Insufficient temperature data returned."
    # Sanity check: should be a plausible summer temperature, not a wrapped/wrong grid cell
    assert df["temp"].between(10, 40).all(), "Implausible temperature values returned."


def test_era5_hourly_wind():
    """
    It should derive wind speed and direction from the u10/v10 components
    """
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
