"""
Meta Data Example
=================
This example demonstrates how to retrieve and display metadata
for a specific weather station using the Meteostat library.
"""

import meteostat as ms

station = ms.stations.meta('72503')  # LaGuardia Airport

print(station)