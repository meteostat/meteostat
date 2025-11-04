import json
from meteostat.parameters import DEFAULT_PARAMETERS
from meteostat.providers.index import DEFAULT_PROVIDERS

PARAMETERS = []
PROVIDERS = []

for parameter in DEFAULT_PARAMETERS:
    PARAMETERS.append({
        "id": parameter.id,
        "name": parameter.name,
        "granularity": parameter.granularity,
        "unit": parameter.unit,
        "dtype": parameter.dtype,
    })

for provider in DEFAULT_PROVIDERS:
    PROVIDERS.append({
        "id": provider.id,
        "name": provider.name,
        "granularity": provider.granularity,
        "parameters": provider.parameters
    })

# Convert parameters to JSON
with open('./parameters.json', 'w') as f:
    json.dump(PARAMETERS, f, indent=2)

# Convert providers to JSON
with open('./providers.json', 'w') as f:
    json.dump(PROVIDERS, f, indent=2)