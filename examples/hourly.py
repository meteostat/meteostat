"""
Hourly Data Example
==================
This example demonstrates how to retrieve and display hourly weather data
for a specific weather station over a defined time period using the
Meteostat library.
"""

from datetime import datetime
import meteostat as ms

# Set time period
start = datetime(2018, 1, 1)
end = datetime(2018, 12, 31, 23, 59)

# Get hourly data
ts = ms.hourly(ms.Station(id='72219'), start, end)
df = ts.fetch()

# Print DataFrame
print(df)