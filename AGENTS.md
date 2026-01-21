# Agent Instructions

Meteostat is a platform which provides access to historical weather and climate data for thousands of weather stations worldwide. This package is the center of the project and features a Python client for accessing station information and time series data. It also contains logic for accessing meteorological data directly from the original data providers.

## Setup & Commands

This project uses Poetry.

- `poetry install` – install dependencies
- `poetry run python3 examples/hourly.py` – run a sample script
- `poetry run pytest tests/unit/ tests/integration/` – run unit & integration tests
- `poetry run ruff check .` – lint all Python files
- `poetry run ruff format .` – auto-format all Python files
- `poetry run ty check .` – check typing

## Specifications

You **MUST** consider the following specifications when working on this project. If your changes affect the foundations outlined under `./specs`, you **MUST** update the specification accordingly. You **MUST ONLY** mention important facts in these specifications. Focus on the **WHAT** and the **WHY**. **DON'T** include implementation details in specifications. 

**ALWAYS** scan the following index and read the associated specification files for fruther instructions:

- `specs/interpolation.md` – Spatial interpolation of multi-station time series data