"""
ERA5 Example
==================
This example demonstrates how to fetch ERA5-Land reanalysis data (0.1-degree
resolution) for an arbitrary coordinate over a defined time period using the
Meteostat library.

Requires a free Climate Data Store (CDS) personal API key
(https://cds.climate.copernicus.eu) with the ERA5-Land dataset's licence
accepted once at https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land.
Set it via the CDS_API_KEY environment variable.
"""

import os
from datetime import datetime
import meteostat as ms

# Set your CDS API key (see https://cds.climate.copernicus.eu, under your profile)
ms.config.copernicus_cds_api_key = os.environ["CDS_API_KEY"]

# Define the location (latitude, longitude) for which to retrieve data
# Points work with ERA5 since it's a global reanalysis grid, not a station network
location = ms.Point(50.2167, 8.45, 805)

# Set time period
start = datetime(2018, 1, 1)
end = datetime(2018, 1, 1, 23, 59)

# Get hourly data
ts = ms.hourly(location, start, end, providers=[ms.Provider.ERA5])
df = ts.fetch()

# Print DataFrame
print(df)
