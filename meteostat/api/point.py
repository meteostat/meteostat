"""
Point Class

A geographical point used for querying nearby weather stations and spatial interpolation.
"""

from typing import Optional


class Point:
    """
    A geographical point
    """

    latitude: float
    longitude: float
    elevation: Optional[int]

    def __init__(
        self, latitude: float, longitude: float, elevation: Optional[int] = None
    ) -> None:
        if latitude < -90 or latitude > 90:
            raise ValueError("Latitude must be between -90 and 90")

        if longitude < -180 or longitude > 180:
            raise ValueError("Longitude must be between -180 and 180")

        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
