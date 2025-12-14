"""
DWD MOSMIX data provider

Parameters: https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_parameteruebersicht.pdf?__blob=publicationFile&v=3
"""

import re
from io import BytesIO
from typing import Optional
from datetime import datetime
from zipfile import ZipFile
from lxml import etree  # type: ignore

import pandas as pd

from meteostat.core.cache import cache_service
from meteostat.enumerations import TTL, Parameter
from meteostat.typing import ProviderRequest
from meteostat.utils.conversions import (
    kelvin_to_celsius,
    ms_to_kmh,
    percentage_to_okta,
    temp_dwpt_to_rhum,
)
from meteostat.core.network import network_service

ENDPOINT = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{station}/kml/MOSMIX_L_LATEST_{station}.kmz"
COCO_MAP = {
    "0": 1,
    "1": 2,
    "2": 3,
    "3": 4,
    "45": 5,
    "49": 5,
    "61": 7,
    "63": 8,
    "65": 9,
    "51": 7,
    "53": 8,
    "55": 9,
    "68": 12,
    "69": 13,
    "71": 14,
    "73": 15,
    "75": 16,
    "80": 17,
    "81": 18,
    "82": 18,
    "83": 19,
    "84": 20,
    "85": 21,
    "86": 22,
    "66": 10,
    "67": 11,
    "56": 10,
    "57": 11,
    "95": 25,
}


def get_coco(code: str | int) -> Optional[int]:
    """
    Map DWD MOSMIX weather condition codes to Meteostat condicodes
    """
    return COCO_MAP.get(str(code))


@cache_service.cache(TTL.HOUR, "pickle")
def get_df(station: str) -> Optional[pd.DataFrame]:
    # Fetch the KMZ file data in memory
    response = network_service.get(ENDPOINT.format(station=station))
    kmz_data = BytesIO(response.content)

    # KMZ -> KML in memory
    with ZipFile(kmz_data, "r") as kmz:
        with kmz.open(kmz.infolist()[0].filename, "r") as raw:
            kml = raw.read()

    # Parse KML
    tree = etree.fromstring(kml)

    # Skip stale forecasts
    issue_time = datetime.strptime(
        tree.xpath(
            "//kml:kml/kml:Document/kml:ExtendedData/"
            + "dwd:ProductDefinition/dwd:IssueTime",
            namespaces=tree.nsmap,
        )[0].text,
        "%Y-%m-%dT%H:%M:%S.%fZ",
    )
    if (datetime.now() - issue_time).total_seconds() > 25200:
        return None

    # Collect all time steps
    timesteps = []
    for step in tree.xpath(
        "//kml:kml/kml:Document/kml:ExtendedData/dwd:ProductDefinition/"
        + "dwd:ForecastTimeSteps/dwd:TimeStep",
        namespaces=tree.nsmap,
    ):
        timesteps.append(step.text)

    # COLLECT WEATHER DATA
    # Each parameter is processed individually
    data = {
        "time": timesteps,
        Parameter.TEMP: [],
        Parameter.DWPT: [],
        Parameter.PRCP: [],
        Parameter.WDIR: [],
        Parameter.WSPD: [],
        Parameter.WPGT: [],
        Parameter.TSUN: [],
        Parameter.PRES: [],
        Parameter.CLDC: [],
        Parameter.VSBY: [],
        Parameter.COCO: [],
    }
    placemark = tree.xpath(
        "//kml:kml/kml:Document/kml:Placemark", namespaces=tree.nsmap
    )[0]

    # Pressure
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="PPPP"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.PRES].append(
            float(value) / 100
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Air temperature
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="TTT"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.TEMP].append(
            kelvin_to_celsius(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Dew point
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="Td"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.DWPT].append(
            kelvin_to_celsius(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Wind direction
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="DD"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.WDIR].append(
            int(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Wind speed
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="FF"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.WSPD].append(
            ms_to_kmh(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Peak wind gust
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="FX1"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.WPGT].append(
            ms_to_kmh(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Weather condition
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="ww"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.COCO].append(
            get_coco(int(float(value)))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Precipitation
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="RR1c"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.PRCP].append(
            float(value) if value.lstrip("-").replace(".", "", 1).isdigit() else None
        )

    # Sunshine Duration
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="SunD1"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.TSUN].append(
            float(value) / 60
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Cloud Cover
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="N"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.CLDC].append(
            percentage_to_okta(float(value))
            if value.lstrip("-").replace(".", "", 1).isdigit()
            else None
        )

    # Visibility
    for value in (
        re.sub(
            r"/\s+/",
            " ",
            placemark.xpath(
                'kml:ExtendedData/dwd:Forecast[@dwd:elementName="VV"]/dwd:value',
                namespaces=tree.nsmap,
            )[0].text,
        )
        .strip()
        .split()
    ):
        data[Parameter.VSBY].append(
            float(value) if value.lstrip("-").replace(".", "", 1).isdigit() else None
        )

    # Convert data dict to DataFrame
    df = pd.DataFrame.from_dict(data)

    # Convert time strings to datetime
    df["time"] = pd.to_datetime(df["time"])

    # Calculate humidity data
    df[Parameter.RHUM] = df.apply(temp_dwpt_to_rhum, axis=1)

    # Set index
    df = df.set_index(["time"])

    # Round decimals
    df = df.round(1)

    # Remove tz awareness
    df = df.tz_convert(None, level="time")

    return df


def fetch(req: ProviderRequest) -> Optional[pd.DataFrame]:
    if "mosmix" in req.station.identifiers:
        return get_df(req.station.identifiers["mosmix"])
