from typing import Optional, Union
from urllib.error import HTTPError

import pandas as pd

from meteostat.core.cache import cache_service
from meteostat.core.logger import logger
from meteostat.enumerations import TTL, Parameter
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import percentage_to_okta

ENDPOINT = "https://opendata.dwd.de/weather/weather_reports/poi/{station}-BEOB.csv"
# TODO: add col 11 for solar radiation support (Globalstrahlung)
USECOLS = [0, 1, 2, 9, 14, 21, 22, 23, 33, 35, 36, 37, 40, 41]
NAMES = {
    "Wolkenbedeckung": Parameter.CLDC,
    "Temperatur (2m)": Parameter.TEMP,
    "Sichtweite": Parameter.VSBY,
    "Windgeschwindigkeit": Parameter.WSPD,
    "Windboen (letzte Stunde)": Parameter.WPGT,
    "Niederschlag (letzte Stunde)": Parameter.PRCP,
    "Relative Feuchte": Parameter.RHUM,
    "Windrichtung": Parameter.WDIR,
    "Druck (auf Meereshoehe)": Parameter.PRES,
    "Sonnenscheindauer (letzte Stunde)": Parameter.TSUN,
    "aktuelles Wetter": Parameter.COCO,
    "Schneehoehe": Parameter.SNWD,
}
COCO_MAP = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "11": 11,
    "12": 12,
    "13": 13,
    "14": 14,
    "15": 15,
    "16": 16,
    "17": 24,
    "18": 17,
    "19": 18,
    "20": 19,
    "21": 20,
    "22": 21,
    "23": 22,
    "24": 19,
    "25": 20,
    "26": 23,
    "27": 25,
    "28": 26,
    "29": 25,
    "30": 26,
    "31": 27,
}


def get_coco(code: str | int) -> Union[int, None]:
    """
    Map DWD POI weather condition codes to Meteostat condicodes
    """
    return COCO_MAP.get(str(code))


@cache_service.cache(TTL.HOUR, "pickle")
def get_df(station: str) -> Optional[pd.DataFrame]:
    try:
        # Read CSV data from DWD server
        df = pd.read_csv(  # type: ignore
            ENDPOINT.format(station=station),
            sep=";",
            skiprows=2,
            na_values="---",
            usecols=USECOLS,
            decimal=",",
        )

        # Rename columns
        df = df.rename(columns=NAMES)

        # Snow cm -> mm
        df[Parameter.SNWD] = df[Parameter.SNWD].multiply(10)
        df[Parameter.VSBY] = df[Parameter.VSBY].multiply(1000)

        # Change coco
        df[Parameter.COCO] = df[Parameter.COCO].apply(get_coco)
        df[Parameter.CLDC] = df[Parameter.CLDC].apply(percentage_to_okta)

        # Set index
        df["time"] = pd.to_datetime(
            df["Datum"] + " " + df["Uhrzeit (UTC)"], format="%d.%m.%y %H:%M"
        )
        df = df.set_index(["time"])
        df = df.drop(["Datum", "Uhrzeit (UTC)"], axis=1)

        return df

    except HTTPError as error:
        logger.info(
            f"Couldn't load DWD POI data for weather station {station} (status: {error.status})"
        )
        return None

    except Exception as error:
        logger.warning(error)
        return None


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if "wmo" in req.station.identifiers:
        return get_df(req.station.identifiers["wmo"])
