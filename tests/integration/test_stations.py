from meteostat import stations
from meteostat.api.point import Point


def test_stations_meta(mock_stations_database):
    station_data = stations.meta("10637")
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


def test_stations_nearby(mock_stations_database):
    nearby_stations = stations.nearby(Point(50.05, 8.6), limit=3)
    assert len(nearby_stations) == 3

    # First station should be the closest (Frankfurt Airport)
    station_1 = nearby_stations.iloc[0]
    assert nearby_stations.index[0] == "10637"
    assert station_1["name"] == "Frankfurt Airport"
    assert station_1["country"] == "DE"
    assert station_1["region"] == "HE"
    assert station_1["elevation"] == 111
    assert station_1["timezone"] == "Europe/Berlin"
    assert station_1["distance"] == 0.0

    # Second station (Frankfurt Westend)
    station_2 = nearby_stations.iloc[1]
    assert nearby_stations.index[1] == "D1424"
    assert station_2["name"] == "Frankfurt  Westend"
    assert station_2["country"] == "DE"
    assert station_2["elevation"] == 124
    assert 9000 < station_2["distance"] < 11000

    # Third station (Egelsbach / Erzhausen)
    station_3 = nearby_stations.iloc[2]
    assert nearby_stations.index[2] == "EDFE0"
    assert station_3["name"] == "Egelsbach / Erzhausen"
    assert station_3["country"] == "DE"
    assert station_3["elevation"] == 117
    assert 10000 < station_3["distance"] < 11000


def test_stations_inventory(mock_stations_database):
    inventory = stations.inventory("10637")
    assert inventory.df is not None
    assert len(inventory.df) == 76
    assert inventory.parameters is not None
    assert len(inventory.parameters) == 15
    assert inventory.start is not None
    assert inventory.start.year == 1931
    assert inventory.end is not None
    assert inventory.end.year == 2025


def test_stations_query():
    df = stations.query("SELECT id FROM stations WHERE country = 'US'")
    assert len(df) == 2701
