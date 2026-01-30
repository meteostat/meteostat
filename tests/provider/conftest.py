"""
Shared fixtures and configuration for provider tests
"""

import logging

import pytest

import meteostat as ms

# Enable DEBUG level logging for meteostat during provider tests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("meteostat").setLevel(logging.DEBUG)


@pytest.fixture(autouse=True)
def disable_cache():
    """Disable cache for all provider tests."""
    ms.config.cache_enable = False
    yield
    ms.config.cache_enable = True
