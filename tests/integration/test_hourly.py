from datetime import datetime
import os

import pandas as pd
import meteostat as ms


def test_hourly(mocker):
    """
    It returns a filtered DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.hourly.fetch")

    mock_fetch.return_value = pd.read_pickle(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fixtures",
            "df_hourly.pickle",
        )
    )
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    df = ts.fetch()

    assert len(df) == 3
    assert df.iloc[0]["temp"] == 8.3


def test_hourly_timezone(mocker):
    """
    It should consider the timezone when filtering the DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.hourly.fetch")

    mock_fetch.return_value = pd.read_pickle(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fixtures",
            "df_hourly.pickle",
        )
    )
    ts = ms.hourly(
        "10637",
        datetime(2024, 1, 1, 15),
        datetime(2024, 1, 1, 17),
        timezone="Europe/Berlin",
    )
    df = ts.fetch()

    assert len(df) == 3
    assert df.iloc[0]["temp"] == 8.5


def test_hourly_none(mocker):
    """
    It returns None if provider returns an empty DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.hourly.fetch")
    mock_fetch.return_value = pd.DataFrame()
    ts = ms.hourly("10637", datetime(2024, 1, 1, 15), datetime(2024, 1, 1, 17))
    assert ts.fetch() is None