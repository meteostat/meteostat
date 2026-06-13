"""
Shared fixtures and configuration for provider tests
"""

import logging

import pytest
import requests

import meteostat as ms

# Enable DEBUG level logging for meteostat during provider tests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("meteostat").setLevel(logging.DEBUG)


def pytest_collection_modifyitems(items):
    """Skip ECCC tests when api.weather.gc.ca is unreachable."""
    eccc_items = [item for item in items if "eccc" in item.nodeid]
    if not eccc_items:
        return
    try:
        requests.get("https://api.weather.gc.ca", timeout=5)
    except requests.exceptions.RequestException:
        skip = pytest.mark.skip(reason="ECCC API (api.weather.gc.ca) is unreachable")
        for item in eccc_items:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def disable_cache():
    """Disable cache for all provider tests."""
    ms.config.cache_enable = False
    yield
    ms.config.cache_enable = True
