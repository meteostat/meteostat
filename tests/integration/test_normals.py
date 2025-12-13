import os

import pandas as pd
import meteostat as ms


def test_normals(mocker):
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
    ts = ms.normals("10637", 2005, 2015)
    df = ts.fetch()

    assert len(df) == 12
    assert df.iloc[0]["temp"] == 2.3


def test_monthly_none(mocker):
    """
    It returns None if provider returns an empty DataFrame
    """
    mock_fetch = mocker.patch("meteostat.providers.meteostat.monthly.fetch")
    mock_fetch.return_value = pd.DataFrame()
    ts = ms.normals("10637", 2005, 2015)
    assert ts.fetch() is None
