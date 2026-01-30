"""
Shared fixtures and configuration for provider tests
"""

import logging

# Enable DEBUG level logging for meteostat during provider tests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("meteostat").setLevel(logging.DEBUG)
