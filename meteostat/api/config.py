"""
Configuration Service

Manages configuration settings for Meteostat, including cache, network,
stations, interpolation, and provider-specific settings. Configuration can be
loaded from environment variables with the MS_ prefix.
"""

import os
import json
from typing import Any, List, Optional

from meteostat.core.logger import logger
from meteostat.enumerations import TTL, Parameter
from meteostat.utils.types import extract_property_type, validate_parsed_value


class ConfigService:
    """
    Configuration Service for Meteostat
    """

    prefix: str

    # Sentinel value to indicate we should skip this env var (distinct from None)
    _SKIP_VALUE = object()

    @property
    def _prefix(self) -> str:
        """
        The environment variable prefix
        """
        return f"{self.prefix}_" if self.prefix else ""

    def _parse_env_value(self, key: str, value: str) -> Any:
        """
        Parse an environment variable value and validate against property type.

        For string types, the value is used directly without JSON parsing.
        For other types (bool, int, list, dict), JSON parsing is used.

        If validation fails, the error is logged and a sentinel value (_SKIP_VALUE)
        is returned to skip the invalid environment variable without aborting initialization.

        Returns None if the environment variable value is explicitly set to null.
        """
        # Extract the expected type for the property
        try:
            expected_type, original_type = extract_property_type(self.__class__, key)
        except ValueError:
            # Property doesn't exist on this config class, skip it
            logger.debug(
                "Environment variable '%s' does not match any config property", key
            )
            return self._SKIP_VALUE

        if expected_type is None:
            # Fallback to JSON parsing if no type annotation is available
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.error("Failed to parse environment variable '%s'", key)
                return self._SKIP_VALUE

        # For string types, use the value directly without JSON parsing
        if expected_type is str:
            return value

        # Parse the value using JSON for non-string types
        try:
            parsed_value = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.error("Failed to parse environment variable '%s'", key)
            return self._SKIP_VALUE

        # Validate and potentially convert the parsed value
        try:
            return validate_parsed_value(
                parsed_value, expected_type, original_type, key
            )
        except (ValueError, TypeError) as e:
            logger.error(
                "Failed to validate environment variable '%s': %s", key, str(e)
            )
            return self._SKIP_VALUE

    def _set_env_value(self, key: str, value: Any) -> None:
        """
        Set a configuration using a key-value pair
        """
        setattr(self, key, value)

    def __init__(self, prefix: str = "MS") -> None:
        """
        Initialize configuration service
        """
        self.prefix = prefix
        self.load_env()

    def get_env_name(self, key: str) -> str:
        """
        Get the environment variable name for a given key
        """
        if not hasattr(self, key):
            raise KeyError(f"Configuration has no key '{key}'")

        key = f"{self._prefix}{key}"
        return key.upper()

    def load_env(self) -> None:
        """
        Update configuration from environment variables with a given prefix.
        """
        for key, value in os.environ.items():
            if not key.startswith(self._prefix):
                continue

            key = key.replace(self._prefix, "").lower()
            value = self._parse_env_value(key, value)

            # Skip invalid values (but allow None to be set explicitly)
            if value is not self._SKIP_VALUE:
                self._set_env_value(key, value)


class Config(ConfigService):
    """
    Meteostat Configuration

    Manages all configuration settings including cache, network, stations,
    interpolation, and provider-specific settings. Supports loading configuration
    from environment variables.
    """

    # General settings
    block_large_requests: bool = True  # Block requests that include too many stations

    # Cache settings
    cache_enable: bool = True
    cache_directory: str = (
        os.path.expanduser("~") + os.sep + ".meteostat" + os.sep + "cache"
    )
    cache_ttl: int = TTL.MONTH
    cache_autoclean: bool = True

    # Network settings
    network_proxies: Optional[dict] = None

    # Station meta data settings
    stations_db_ttl: int = TTL.WEEK
    stations_db_endpoints: List[str] = [
        "https://data.meteostat.net/stations.db",
        "https://raw.githubusercontent.com/meteostat/weather-stations/master/stations.db",
    ]
    stations_db_file: str = (
        os.path.expanduser("~") + os.sep + ".meteostat" + os.sep + "stations.db"
    )

    # Interpolation settings
    lapse_rate_parameters = [Parameter.TEMP, Parameter.TMIN, Parameter.TMAX]

    # [Provider] Meteostat settings
    include_model_data: bool = True
    hourly_endpoint: str = "https://data.meteostat.net/hourly/{year}/{station}.csv.gz"
    daily_endpoint: str = "https://data.meteostat.net/daily/{year}/{station}.csv.gz"
    monthly_endpoint: str = "https://data.meteostat.net/monthly/{station}.csv.gz"

    # [Provider] DWD settings
    dwd_ftp_host: str = "opendata.dwd.de"
    dwd_hourly_modes: Optional[List[str]] = None
    dwd_daily_modes: Optional[List[str]] = None
    dwd_climat_modes: Optional[List[str]] = None

    # [Provider] NOAA settings
    aviationweather_endpoint: str = (
        "https://aviationweather.gov/api/data/metar?"
        "ids={station}&format=raw&taf=false&hours=24"
    )
    aviationweather_user_agent: Optional[str] = None

    # [Provider] Met.no settings
    metno_forecast_endpoint: str = (
        "https://api.met.no/weatherapi/locationforecast/2.0/compact?"
        "lat={latitude}&lon={longitude}&altitude={elevation}"
    )
    metno_user_agent: Optional[str] = None

    # [Provider] GSA settings
    gsa_api_base_url: str = "https://dataset.api.hub.geosphere.at/v1"


config = Config("MS")
