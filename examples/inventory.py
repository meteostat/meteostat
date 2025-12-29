"""
Inventory Example
=================
This example demonstrates how to retrieve and display the data inventory
for a specific weather station using the Meteostat library.
"""

import meteostat as ms

STATION = '71624'  # Toronto Pearson International Airport

# Get station inventory
inventory = ms.stations.inventory(STATION)

print(f"Data available from {inventory.start} to {inventory.end}.")