from meteostat import station


def test_station(mock_station):
    """
    It fetches station data correctly
    """
    station_data = station("10637")
    assert station_data is not None
    assert station_data.id == "10637"
    assert station_data.name == "Frankfurt Airport"
    assert station_data.country == "DE"
    assert station_data.latitude == 50.05
    assert station_data.longitude == 8.6
    assert station_data.elevation == 111
    assert station_data.timezone == "Europe/Berlin"
    assert station_data.identifiers["wmo"] == "10637"
    assert station_data.identifiers["icao"] == "EDDF"
