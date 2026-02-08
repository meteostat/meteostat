# Meteostat Python – Developer Instructions

Meteostat is a Python library for accessing and analyzing historical weather and climate data. It provides a clean API for fetching meteorological data from multiple providers (DWD, NOAA, ECCC, GSA, Met.no, etc.) and includes features for data interpolation, aggregation, and unit conversions. The mission: "Make historical weather and climate data easily accessible to everyone".

## Philosophy

- Say 'I don't know' if you don't know. Answer only if confident. Think before responding.
- Follow strict TDD. Red-Green-Refactor. Write the failing test first. Always.
- Simple over clever. Readability first. Small functions. Single responsibility.

## Important Notes

- Always use `poetry install --all-groups` to install dependencies
- Do NOT run provider tests (`tests/provider/`) for regular PRs
- Use `ty` for type checking, not `mypy` or `pyright`
- Import from `meteostat`, not submodules directly
- ALWAYS run `poetry run ruff format .` before committing
- ALWAYS run `poetry run pytest tests/unit tests/integration -v` before committing