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

    # Register the math functions
    # This works regardless of whether SQLite was compiled with ENABLE_MATH_FUNCTIONS
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


class TestAcosDomainClamping:
    """Test that acos argument is clamped to [-1, 1] to handle floating-point edge cases."""

    def test_north_pole_query_no_error(self):
        """
        Querying nearby stations from North Pole should not raise math domain error.

        Float precision can cause acos to receive values slightly > 1.
        """
        stations = Stations()
        conn = sqlite3.connect(":memory:")
        stations._register_math_functions(conn)

        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE stations (
                id TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL
            )
        """)

        # Insert station at the pole
        cursor.execute(
            "INSERT INTO stations VALUES (?, ?, ?)",
            ("POLE1", 90.0, 0.0),
        )
        conn.commit()

        # Query from exact same point - this can cause acos(1.0000001) error
        sql = """
            SELECT id,
                6371000 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(:lon)) + 
                    sin(radians(:lat)) * sin(radians(latitude))
                ) AS distance
            FROM stations
        """

        # Should not raise - if it does, the clamping is not working
        cursor.execute(sql, {"lat": 90.0, "lon": 0.0})
        result = cursor.fetchone()
        assert result is not None
        # Distance to same point should be 0 (or very close)
        assert result[1] < 1, f"Distance to same point should be ~0, got {result[1]}"

        conn.close()

    def test_antipodal_query_no_error(self):
        """
        Querying between antipodal points should not raise math domain error.

        Float precision can cause acos to receive values slightly < -1.
        """
        stations = Stations()
        conn = sqlite3.connect(":memory:")
        stations._register_math_functions(conn)

        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE stations (
                id TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL
            )
        """)

        cursor.execute(
            "INSERT INTO stations VALUES (?, ?, ?)",
            ("TEST1", 45.0, 0.0),
        )
        conn.commit()

        # Query from antipodal point: (-45, 180)
        sql = """
            SELECT id,
                6371000 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(:lon)) + 
                    sin(radians(:lat)) * sin(radians(latitude))
                ) AS distance
            FROM stations
        """

        cursor.execute(sql, {"lat": -45.0, "lon": 180.0})
        result = cursor.fetchone()
        assert result is not None
        # Antipodal distance should be ~20000km
        assert result[1] > 19000000, (
            f"Antipodal distance should be ~20000km, got {result[1]}"
        )

        conn.close()
