"""
Interpolation Example
==================
This example demonstrates how to retrieve hourly weather data from multiple
stations near a specified geographic point and perform spatial interpolation
to estimate weather conditions at that point.
"""

from datetime import date
import meteostat as ms

# Specify location and time range
POINT = ms.Point(50.1155, 8.6842, 113)  # Try with your location
START = date(2018, 1, 1)
END = date(2018, 1, 31)

# Get nearby weather stations
stations = ms.stations.nearby(POINT, limit=4)

# Get daily data & perform interpolation
ts = ms.hourly(stations, START, END)
df = ms.interpolate(ts, POINT).fetch()

print(df)
