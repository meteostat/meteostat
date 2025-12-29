"""
Nearby Weather Stations Example
===============================
This example demonstrates how to retrieve and display nearby weather stations
for a specific geographic point using the Meteostat library.
"""

import meteostat as ms

POINT = ms.Point(50.1155, 8.6842, 113)  # Try with your location

# Get nearby weather stations
stations = ms.stations.nearby(POINT, limit=4)

print(stations)