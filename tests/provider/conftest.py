"""
Shared fixtures and configuration for provider tests
"""

import logging
import os

import pytest
import requests

import meteostat as ms

# Enable DEBUG level logging for meteostat during provider tests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("meteostat").setLevel(logging.DEBUG)


def pytest_collection_modifyitems(items):
    """Skip ECCC tests when api.weather.gc.ca is unreachable, and ERA5 tests when no CDS API key is configured."""
    eccc_items = [item for item in items if "eccc" in item.nodeid]
    if eccc_items:
        try:
            requests.get("https://api.weather.gc.ca", timeout=5)
        except requests.exceptions.RequestException:
            skip = pytest.mark.skip(
                reason="ECCC API (api.weather.gc.ca) is unreachable"
            )
            for item in eccc_items:
                item.add_marker(skip)

    era5_items = [item for item in items if "era5" in item.nodeid]
    if era5_items and not os.environ.get("CDS_API_KEY"):
        skip = pytest.mark.skip(reason="CDS_API_KEY is not set")
        for item in era5_items:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def disable_cache():
    """Disable cache for all provider tests."""
    ms.config.cache_enable = False
    yield
    ms.config.cache_enable = True
