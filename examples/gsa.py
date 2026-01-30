"""
GeoSphere Austria Example
==================
This example demonstrates how to fetch weather data from the
GeoSphere Austria Data Hub for a specific weather station over a defined
time period using the Meteostat library.
"""

from datetime import datetime
import meteostat as ms

# Set time period
start = datetime(2018, 1, 1)
end = datetime(2018, 12, 31, 23, 59)

# Get hourly data
print("=== GeoSphere Austria Hourly Data ===")
ts = ms.hourly("11155", start, end, providers=[ms.Provider.GSA_HOURLY])
df = ts.fetch()
print(df)

# Get synoptic data
print("\n=== GeoSphere Austria Synoptic Data ===")
ts = ms.hourly("11155", start, end, providers=[ms.Provider.GSA_SYNOP])
df = ts.fetch()
print(df)

# Get daily data
print("\n=== GeoSphere Austria Daily Data ===")
ts = ms.daily("11155", start, end, providers=[ms.Provider.GSA_DAILY])
df = ts.fetch()
print(df)

# Get monthly data
print("\n=== GeoSphere Austria Monthly Data ===")
ts = ms.monthly("11155", start, end, providers=[ms.Provider.GSA_MONTHLY])
df = ts.fetch()
print(df)
