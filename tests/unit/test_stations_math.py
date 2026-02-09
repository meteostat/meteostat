"""
Unit tests for Stations math function registration
"""

import math
import sqlite3

from meteostat.api.stations import Stations


def test_register_math_functions():
    """Test that math functions are properly registered in SQLite"""
    stations = Stations()
    conn = sqlite3.connect(":memory:")

    # Before registration, unregister any existing functions to simulate
    # an SQLite installation without math functions
    # (Note: We can't truly unregister in Python's sqlite3, but we can test registration)

    # Register the math functions
    stations._register_math_functions(conn)

    # Test acos
    cursor = conn.cursor()
    cursor.execute("SELECT acos(0.5)")
    result = cursor.fetchone()[0]
    expected = math.acos(0.5)
    assert abs(result - expected) < 1e-10, f"acos(0.5) = {result}, expected {expected}"

    # Test cos
    cursor.execute("SELECT cos(1.5708)")  # approximately pi/2
    result = cursor.fetchone()[0]
    expected = math.cos(1.5708)
    assert abs(result - expected) < 1e-4

    # Test sin
    cursor.execute("SELECT sin(1.5708)")  # approximately pi/2
    result = cursor.fetchone()[0]
    expected = math.sin(1.5708)
    assert abs(result - expected) < 1e-4

    # Test radians
    cursor.execute("SELECT radians(180)")
    result = cursor.fetchone()[0]
    expected = math.pi
    assert abs(result - expected) < 1e-10

    # Test degrees
    cursor.execute("SELECT degrees(?)", (math.pi,))
    result = cursor.fetchone()[0]
    expected = 180.0
    assert abs(result - expected) < 1e-10

    conn.close()


def test_haversine_distance_calculation():
    """Test the complete haversine distance calculation using registered math functions"""
    stations = Stations()
    conn = sqlite3.connect(":memory:")

    # Register math functions
    stations._register_math_functions(conn)

    # Create a simple test table
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE test_stations (
            id TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    # Insert test data: Frankfurt coordinates
    cursor.execute(
        "INSERT INTO test_stations VALUES (?, ?, ?)", ("TEST1", 50.1155, 8.6842)
    )
    conn.commit()

    # Test the distance calculation query (same as used in nearby())
    lat = 50.05
    lon = 8.6
    sql = """
        SELECT
            id,
            ROUND(
                (
                    6371000 * acos(
                        cos(radians(:lat)) * cos(radians(latitude)) * 
                        cos(radians(longitude) - radians(:lon)) + 
                        sin(radians(:lat)) * sin(radians(latitude))
                    )
                ),
                1
            ) AS distance
        FROM test_stations
    """

    cursor.execute(sql, {"lat": lat, "lon": lon})
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "TEST1"

    # Distance should be approximately 10km
    distance = result[1]
    assert 9000 < distance < 11000, f"Distance = {distance}, expected ~10000m"

    conn.close()
