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

from meteostat.enumerations import TTL, Parameter
from meteostat.typing import ProviderRequest
from meteostat.core.cache import cache_service
from meteostat.utils.conversions import ms_to_kmh
from meteostat.providers.dwd.shared import get_ftp_connection


BASE_DIR = "/climate_environment/CDC/observations_germany/climate/monthly/kl/"
USECOLS = [1, 4, 5, 6, 7, 9, 10, 11, 12, 14]  # CSV cols which should be read
PARSE_DATES = {"time": [0]}  # Which columns should be parsed as dates?
NAMES = {
    "MO_N": Parameter.CLDC,
    "MO_TT": Parameter.TEMP,
    "MO_TX": Parameter.TMAX,
    "MO_TN": Parameter.TMIN,
    "MX_TX": Parameter.TXMX,
    "MX_TN": Parameter.TXMN,
    "MX_FX": Parameter.WPGT,
    "MO_SD_S": Parameter.TSUN,
    "MO_RR": Parameter.PRCP,
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


@cache_service.cache(TTL.WEEK, "pickle")
def get_df(station: str, mode: str) -> Optional[pd.DataFrame]:
    """
    Get a file from DWD FTP server and convert to Polars DataFrame
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
        parse_dates=PARSE_DATES,
        engine="python",
    )

    # Rename columns
    df = df.rename(columns=lambda x: x.strip())
    df = df.rename(columns=NAMES)

    # Convert data
    df["wpgt"] = df["wpgt"].apply(ms_to_kmh)
    df["tsun"] = df["tsun"] * 60
    df["tsun"] = df["tsun"].round()
    df["cldc"] = df["cldc"].round()

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
            mode,
        )
        for mode in modes
    ]

    df = pd.concat(data)

    return df.loc[~df.index.duplicated(keep="first")]
