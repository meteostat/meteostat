from datetime import datetime
import os

import pandas as pd
import meteostat as ms


def test_monthly(mocker):
    """
    It returns a filtered DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.monthly.fetch")
    mock_fetch.return_value = pd.read_pickle(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fixtures",
            "df_monthly.pickle",
        )
    )
    ts = ms.monthly("10637", datetime(2015, 1, 1), datetime(2018, 12, 31))
    df = ts.fetch()

    assert len(df) == 48
    assert df.iloc[0]["temp"] == 3.1


def test_monthly_none(mocker):
    """
    It returns None if provider returns an empty DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.monthly.fetch")
    mock_fetch.return_value = pd.DataFrame()
    ts = ms.monthly("10637", datetime(2015, 1, 1), datetime(2018, 12, 31))
    assert ts.fetch() is None
