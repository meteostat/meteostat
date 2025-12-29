"""
Line Chart Example
==================
This example demonstrates how to create a line chart using Matplotlib
to visualize average, minimum, and maximum temperature data for a specific
location over a defined time period.

This example requires the Matplotlib library.
"""

from datetime import date
import matplotlib.pyplot as plt
import meteostat as ms

# Specify location and time range
POINT = ms.Point(50.1155, 8.6842, 113)  # Try with your location
START = date(2018, 1, 1)
END = date(2018, 12, 31)

# Get nearby weather stations
stations = ms.stations.nearby(POINT, limit=4)

# Get daily data & perform interpolation
ts = ms.daily(stations, START, END)
df = ms.interpolate(ts, POINT)

# Plot line chart including average, minimum and maximum temperature
df.plot(y=[ms.Parameter.TEMP, ms.Parameter.TMIN, ms.Parameter.TMAX])
plt.show()
