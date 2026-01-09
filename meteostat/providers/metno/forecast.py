from typing import Optional, Union
from urllib.error import HTTPError

import pandas as pd

from meteostat.api.config import config
from meteostat.enumerations import TTL, Parameter
from meteostat.core.logger import logger
from meteostat.core.network import network_service
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import percentage_to_okta
from meteostat.core.cache import cache_service


ENDPOINT = config.metno_forecast_endpoint
USER_AGENT = config.metno_user_agent
CONDICODES = {
    "clearsky": 1,
    "cloudy": 3,
    "fair": 2,
    "fog": 5,
    "heavyrain": 9,
    "heavyrainandthunder": 26,
    "heavyrainshowers": 18,
    "heavyrainshowersandthunder": 26,
    "heavysleet": 13,
    "heavysleetandthunder": 26,
    "heavysleetshowers": 20,
    "heavysleetshowersandthunder": 26,
    "heavysnow": 16,
    "heavysnowandthunder": 26,
    "heavysnowshowers": 22,
    "heavysnowshowersandthunder": 26,
    "lightrain": 7,
    "lightrainandthunder": 25,
    "lightrainshowers": 17,
    "lightrainshowersandthunder": 25,
    "lightsleet": 12,
    "lightsleetandthunder": 25,
    "lightsleetshowers": 19,
    "lightsnow": 14,
    "lightsnowandthunder": 25,
    "lightsnowshowers": 21,
    "lightssleetshowersandthunder": 25,
    "lightssnowshowersandthunder": 25,
    "partlycloudy": 3,
    "rain": 8,
    "rainandthunder": 25,
    "rainshowers": 17,
    "rainshowersandthunder": 25,
    "sleet": 12,
    "sleetandthunder": 25,
    "sleetshowers": 19,
    "sleetshowersandthunder": 25,
    "snow": 15,
    "snowandthunder": 25,
    "snowshowers": 21,
    "snowshowersandthunder": 25,
}


def get_condicode(code: str) -> Union[int, None]:
    """
    Map Met.no symbol codes to Meteostat condition codes

    Documentation: https://api.met.no/weatherapi/weathericon/2.0/documentation
    """
    return CONDICODES.get(str(code).split("_")[0], None)


def safe_get(data, keys, default=None, transform=lambda x: x):
    """
    Safely get a nested value from a dictionary, with an optional transformation.

    :param data: The dictionary to get the value from.
    :param keys: A list of keys to navigate through the dictionary.
    :param default: The default value to return if any key is missing.
    :param transform: A function to apply to the retrieved value if found.
    :return: The retrieved value or the default.
    """
    for key in keys:
        data = data.get(key)
        if data is None:
            return default
    return transform(data)


def map_data(record):
    """
    Map Met.no JSON data to Meteostat column names
    """
    details_instant = ["data", "instant", "details"]
    details_next_1_hour = ["data", "next_1_hours", "details"]

    return {
        "time": record["time"],
        Parameter.TEMP: safe_get(record, details_instant + ["air_temperature"]),
        Parameter.CLDC: safe_get(
            record,
            details_instant + ["cloud_area_fraction"],
            transform=percentage_to_okta,
        ),
        Parameter.RHUM: safe_get(record, details_instant + ["relative_humidity"]),
        Parameter.PRCP: safe_get(
            record, details_next_1_hour + ["precipitation_amount"]
        ),
        Parameter.WSPD: safe_get(
            record, details_instant + ["wind_speed"], transform=lambda x: x * 3.6
        ),
        Parameter.WPGT: safe_get(
            record,
            details_instant + ["wind_speed_of_gust"],
            transform=lambda x: x * 3.6,
        ),
        Parameter.WDIR: safe_get(
            record,
            details_instant + ["wind_from_direction"],
            transform=lambda x: int(round(x)),
        ),
        Parameter.PRES: safe_get(
            record, details_instant + ["air_pressure_at_sea_level"]
        ),
        Parameter.COCO: safe_get(
            record,
            ["data", "next_1_hours", "summary", "symbol_code"],
            transform=get_condicode,
        ),
    }


@cache_service.cache(TTL.HOUR, "pickle")
def get_df(latitude: float, longitude: float, elevation: int) -> Optional[pd.DataFrame]:
    file_url = ENDPOINT.format(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
    )

    headers = {"User-Agent": USER_AGENT}

    try:
        response = network_service.get(file_url, headers=headers)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Parse the JSON content into a DataFrame
        data = response.json()

        # Create DataFrame
        df = pd.DataFrame(map(map_data, data["properties"]["timeseries"]))

        # Handle time column & set index
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index(["time"])

        # Remove the UTC timezone from the time index
        df.index = df.index.tz_localize(None)  # type: ignore[union-attr]

        # Shift prcp and coco columns by 1 (as they refer to the next hour)
        df["prcp"] = df["prcp"].shift(1)
        df["coco"] = df["coco"].shift(1)

        return df

    except HTTPError as error:
        logger.warning(
            f"Couldn't load weather forecast from met.no (status: {error.status})"
        )

    except Exception as error:
        logger.error(error, exc_info=True)


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if not USER_AGENT:
        logger.warning(
            "MET Norway requires a unique user agent as per their terms of service. Please use config to specify your user agent. For now, this provider is skipped."
        )
        return None

    return get_df(
        req.station.latitude,
        req.station.longitude,
        req.station.elevation,
    )
