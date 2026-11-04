"""
ERA5 Example
==================
This example demonstrates how to fetch ERA5 reanalysis data for an arbitrary
coordinate (not just a known weather station) over a defined time period
using the Meteostat library.
"""

from datetime import datetime
import meteostat as ms

# Define the location (latitude, longitude) for which to retrieve data
# Points work with ERA5 since it's a global reanalysis grid, not a station network
location = ms.Point(50.3167, 8.5)

# Set time period
start = datetime(2018, 1, 1)
end = datetime(2018, 1, 1, 23, 59)

# Get hourly data
ts = ms.hourly(location, start, end, providers=[ms.Provider.ERA5_HOURLY])
df = ts.fetch()

# Print DataFrame
print(df)
