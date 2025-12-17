from datetime import datetime
from typing import Optional

import pandas as pd

from meteostat.enumerations import TTL, Parameter
from meteostat.core.cache import cache_service
from meteostat.core.network import network_service
from meteostat.providers.eccc.shared import ENDPOINT, get_meta_data
from meteostat.typing import ProviderRequest

BATCH_LIMIT = 9000
PROPERTIES = {
    "LOCAL_DATE": "time",
    "MAX_TEMPERATURE": Parameter.TMAX,
    "MEAN_TEMPERATURE": Parameter.TEMP,
    "MIN_TEMPERATURE": Parameter.TMIN,
    "SPEED_MAX_GUST": Parameter.WPGT,
    "TOTAL_PRECIPITATION": Parameter.PRCP,
    "SNOW_ON_GROUND": Parameter.SNWD,
    "TOTAL_SNOW": Parameter.SNOW,
}


@cache_service.cache(TTL.DAY, "pickle")
def get_df(climate_id: str, year: int) -> Optional[pd.DataFrame]:
    # Process start & end date
    # ECCC uses the station's local time zone
    start = datetime(year, 1, 1, 0, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")
    end = datetime(year, 12, 31, 23, 59, 59).strftime("%Y-%m-%dT%H:%M:%S")

    response = network_service.get(
        f"{ENDPOINT}/collections/climate-daily/items",
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

    # Create a DataFrame from the extracted features
    df = pd.DataFrame(features)
    df = df.rename(columns=PROPERTIES)

    # Handle time column & set index
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index(["time"])

    return df


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if (
        "national" not in req.station.identifiers
        or req.start is None
        or req.end is None
    ):
        return None

    meta_data = get_meta_data(req.station.identifiers["national"])
    climate_id = meta_data.get("CLIMATE_IDENTIFIER")
    archive_first = meta_data.get("DLY_FIRST_DATE")
    archive_last = meta_data.get("DLY_LAST_DATE")

    if not (climate_id and archive_first and archive_last):
        return None

    archive_start = datetime.strptime(archive_first, "%Y-%m-%d %H:%M:%S")
    archive_end = datetime.strptime(archive_last, "%Y-%m-%d %H:%M:%S")

    years = range(
        max(req.start.year, archive_start.year),
        min(req.end.year, archive_end.year) + 1,
    )
    data = [get_df(climate_id, year) for year in years]

    return pd.concat(data) if len(data) and not all(d is None for d in data) else None
