"""
Utilities for geographical calculations.

The code is licensed under the MIT license.
"""

import numpy as np


def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """
    Calculate distance between two geographical points using the Haversine formula
    """
    # Earth radius in meters
    radius = 6371000

    # Degress to radian
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])

    # Deltas
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Calculate distance
    arch = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    arch_sin = 2 * np.arcsin(np.sqrt(arch))

    return round(radius * arch_sin)
