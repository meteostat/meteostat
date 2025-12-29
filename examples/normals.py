"""
Climate Normals Data Example
============================
This example demonstrates how to retrieve and display climate normals data
for a specific weather station over a defined time period using the
Meteostat library.
"""

import meteostat as ms

# Get climate normals data
ts = ms.normals(ms.Station(id='10637'), 1961, 1990)
df = ts.fetch()

# Print DataFrame
print(df)