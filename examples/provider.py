"""
Example: Fetch data from a specific provider
============================================
This example demonstrates how to retrieve and display hourly temperature data
for a specific weather station over a defined time period using the Meteostat
library, directly from the DWD provider.
"""

from datetime import datetime
import meteostat as ms

# Set time period
start = datetime(2018, 1, 1)
end = datetime(2018, 12, 31, 23, 59)

# Get hourly temperature data directly from DWD
ts = ms.hourly(
    "10637",
    start,
    end,
    providers=[ms.Provider.DWD_HOURLY],
    parameters=[ms.Parameter.TEMP],
)
df = ts.fetch()

# Print DataFrame
print(df)
