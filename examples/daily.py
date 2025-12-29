"""
Daily Data Example
==================
This example demonstrates how to retrieve and display daily weather data
for a specific weather station over a defined time period using the
Meteostat library.
"""

from datetime import date
import meteostat as ms

# Set time period
start = date(2018, 1, 1)
end = date(2018, 12, 31)

# Get daily data
ts = ms.daily(ms.Station(id='10637'), start, end)
df = ts.fetch()

# Print DataFrame
print(df)