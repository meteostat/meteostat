"""
DWD national daily data import routine

Get daily data for weather stations in Germany.

The code is licensed under the MIT license.
"""

from datetime import datetime
from ftplib import FTP
from io import BytesIO
from typing import Optional
from zipfile import ZipFile

import pandas as pd

from meteostat.api.config import config
from meteostat.enumerations import TTL, Parameter
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.utils.conversions import ms_to_kmh, pres_to_msl
from meteostat.providers.dwd.shared import get_ftp_connection

BASE_DIR = "/climate_environment/CDC/observations_germany/climate/daily/kl/"
USECOLS = [1, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16]  # CSV cols which should be read
NAMES = {
    "FX": Parameter.WPGT,
    "FM": Parameter.WSPD,
    "RSK": Parameter.PRCP,
    "SDK": Parameter.TSUN,
    "SHK_TAG": Parameter.SNWD,
    "NM": Parameter.CLDC,
    "PM": Parameter.PRES,
    "TMK": Parameter.TEMP,
    "UPM": Parameter.RHUM,
    "TXK": Parameter.TMAX,
    "TNK": Parameter.TMIN,
}


def find_file(ftp: FTP, mode: str, needle: str):
    """
    Find file in directory
    """
    match = None

    try:
        ftp.cwd(BASE_DIR + mode)
        files = ftp.nlst()
        matching = [f for f in files if needle in f]
        match = matching[0]
    except BaseException:
        pass

    return match


@cache_service.cache(TTL.DAY, "pickle")
def get_df(station: str, elevation: int, mode: str) -> Optional[pd.DataFrame]:
    """
    Get a file from DWD FTP server and convert to DataFrame
    """
    ftp = get_ftp_connection()
    remote_file = find_file(ftp, mode, f"_{station}_")

    if remote_file is None:
        return None

    buffer = BytesIO()
    ftp.retrbinary("RETR " + remote_file, buffer.write)

    ftp.close()

    # Unzip file
    with ZipFile(buffer, "r") as zipped:
        filelist = zipped.namelist()
        raw = None
        for file in filelist:
            if file[:7] == "produkt":
                with zipped.open(file, "r") as reader:
                    raw = BytesIO(reader.read())

    # Convert raw data to DataFrame
    df: pd.DataFrame = pd.read_csv(  # type: ignore
        raw,
        sep=r"\s*;\s*",
        date_format="%Y%m%d",
        na_values=["-999", -999],
        usecols=USECOLS,
        engine="python",
    )

    # Rename columns
    df = df.rename(columns=lambda x: x.strip())
    df = df.rename(columns=NAMES)

    # Parse date column (first column contains the date)
    df["time"] = pd.to_datetime(df.iloc[:, 0], format="%Y%m%d")
    df = df.drop(df.columns[0], axis=1)

    # Convert data
    df[Parameter.SNWD] = df[Parameter.SNWD] * 10
    df[Parameter.WPGT] = df[Parameter.WPGT].apply(ms_to_kmh)
    df[Parameter.WSPD] = df[Parameter.WSPD].apply(ms_to_kmh)
    df[Parameter.TSUN] = df[Parameter.TSUN] * 60
    df[Parameter.PRES] = df.apply(lambda row: pres_to_msl(row, elevation), axis=1)

    # Set index
    df = df.set_index("time")

    # Round decimals
    df = df.round(1)

    return df


def fetch(req: ProviderRequest):
    if "national" not in req.station.identifiers:
        return pd.DataFrame()

    # Check which modes to consider for data fetching
    #
    # The dataset is divided into a versioned part with completed quality check ("historical"),
    # and a part for which the quality check has not yet been completed ("recent").
    #
    # There is no definite answer as to when the quality check is completed. We're assuming a
    # period of 3 years here. If the end date of the query is within this period, we will also
    # consider the "recent" mode.
    modes = ["historical"]
    if abs((req.end - datetime.now()).days) < 3 * 365:
        modes.append("recent")

    data = [
        get_df(
            req.station.identifiers["national"],
            req.station.elevation,
            mode,
        )
        for mode in config.dwd_daily_modes or modes
    ]

    df = pd.concat(data)

    return df.loc[~df.index.duplicated(keep="first")]
