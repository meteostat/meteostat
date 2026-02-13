from datetime import datetime
from typing import Optional

import pandas as pd
import pytz

from meteostat.enumerations import TTL, Parameter
from meteostat.core.cache import cache_service
from meteostat.core.logger import logger
from meteostat.core.network import network_service
from meteostat.providers.eccc.shared import ENDPOINT, get_meta_data
from meteostat.typing import ProviderRequest
from meteostat.utils.data import safe_concat

BATCH_LIMIT = 9000

# Map common timezone abbreviations to IANA timezone names
# ECCC stations often use abbreviations that pytz cannot resolve
TZ_ABBREVIATION_MAP = {
    "NST": "America/St_Johns",
    "NDT": "America/St_Johns",
    "AST": "America/Halifax",
    "ADT": "America/Halifax",
    "EST": "America/Toronto",
    "EDT": "America/Toronto",
    "CST": "America/Winnipeg",
    "CDT": "America/Winnipeg",
    "MST": "America/Edmonton",
    "MDT": "America/Edmonton",
    "PST": "America/Vancouver",
    "PDT": "America/Vancouver",
    "YST": "America/Whitehorse",
    "YDT": "America/Whitehorse",
}

PROPERTIES = {
    "UTC_DATE": "time",
    "RELATIVE_HUMIDITY": Parameter.RHUM,
    "WIND_DIRECTION": Parameter.WDIR,
    "WIND_SPEED": Parameter.WSPD,
    "VISIBILITY": Parameter.VSBY,
    "PRECIP_AMOUNT": Parameter.PRCP,
    "TEMP": Parameter.TEMP,
}


@cache_service.cache(TTL.DAY, "pickle")
def get_df(climate_id: str, year: int, tz: str) -> Optional[pd.DataFrame]:
    # Process start & end date
    # ECCC uses the station's local time zone
    from_timezone = pytz.timezone("UTC")
    iana_tz = TZ_ABBREVIATION_MAP.get(tz, tz)
    try:
        to_timezone = pytz.timezone(iana_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone '{tz}' for ECCC station, skipping")
        return None
    start = (
        from_timezone.localize(datetime(year, 1, 1, 0, 0, 0))
        .astimezone(to_timezone)
        .strftime("%Y-%m-%dT%H:%M:%S")
    )
    end = (
        from_timezone.localize(datetime(year, 12, 31, 23, 59, 59))
        .astimezone(to_timezone)
        .strftime("%Y-%m-%dT%H:%M:%S")
    )

    response = network_service.get(
        f"{ENDPOINT}/collections/climate-hourly/items",
        params={
            "CLIMATE_IDENTIFIER": climate_id,
            "datetime": f"{start}/{end}",
            "f": "json",
            "properties": ",".join(PROPERTIES.keys()),
            "limit": BATCH_LIMIT,
        },
    )

    data = response.json()

    # Extract features from the response
    features = map(
        lambda feature: feature["properties"] if "properties" in feature else {},
        data.get("features", []),
    )

    df = pd.DataFrame(features)

    if df.empty:
        return None

    df = df.rename(columns=PROPERTIES)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index(["time"])

    # Convert data units
    df[Parameter.WDIR] = df[Parameter.WDIR] * 10  # Wind direction is provided 10's deg
    df[Parameter.VSBY] = (
        df[Parameter.VSBY] * 1000
    )  # Visibility is provided in kilometres

    return df


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if (
        "national" not in req.station.identifiers
        or req.start is None
        or req.end is None
    ):
        return None

    meta_data = get_meta_data(req.station.identifiers["national"])

    if meta_data is None:
        return None

    climate_id = meta_data.get("CLIMATE_IDENTIFIER")
    archive_first = meta_data.get("HLY_FIRST_DATE")
    archive_last = meta_data.get("HLY_LAST_DATE")
    timezone = meta_data.get("TIMEZONE")

    if not (climate_id and archive_first and archive_last and timezone):
        return None

    archive_start = datetime.strptime(archive_first, "%Y-%m-%d %H:%M:%S")
    archive_end = datetime.strptime(archive_last, "%Y-%m-%d %H:%M:%S")

    years = range(
        max(req.start.year, archive_start.year),
        min(req.end.year, archive_end.year) + 1,
    )
    data = [get_df(climate_id, year, timezone) for year in years]

    return safe_concat(data)
