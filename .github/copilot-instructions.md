# Meteostat Python – Developer Instructions

## Repository Overview

**What it does:** Meteostat is a Python library for accessing and analyzing historical weather and climate data. It provides a clean API for fetching meteorological data from multiple providers (DWD, NOAA, ECCC, GSA, Met.no) and includes features for data interpolation, aggregation, and unit conversions.

**Project details:**
- **Type:** Python package published to PyPI
- **Language:** Python 3.11+
- **Package Manager:** Poetry
- **Build System:** poetry-core
- **Key Dependencies:** pandas, requests, pytz
- **Development Tools:** pytest, ruff (linting), ty (type checking)

## Build and Validation Instructions

### Initial Setup

**ALWAYS run this first when working with this repository:**

```bash
poetry install --all-groups
```

This installs:
- Core dependencies (pandas, requests, pytz)
- Development dependencies (pytest, ruff, ty, pytest-mock)
- Extra dependencies (matplotlib, metar, lxml)

**Important:** The `--all-groups` flag is required to install dev and extras dependencies needed for testing and type checking.

### Running Tests

**ALWAYS run tests in this specific order:**

1. **Unit Tests** (fast):
   ```bash
   poetry run pytest tests/unit -v
   ```
   - Tests conversions, data utilities, geo functions, parsers, validators
   - Must pass before integration tests

2. **Integration Tests** (moderate):
   ```bash
   poetry run pytest tests/integration -v
   ```
   - Tests API functions: daily, hourly, monthly, normals, interpolate, merge

3. **Provider Tests** (scheduled nightly, not required for PRs):
   ```bash
   poetry run pytest tests/provider -v -s
   ```
   - Tests external data providers (DWD, NOAA, ECCC, GSA, Met.no)
   - Only run automatically in CI on schedule
   - **Do NOT run these for regular PRs** - they test external APIs

### Linting

**ALWAYS run before committing code changes:**

```bash
ruff check meteostat/ tests/
```

- Uses ruff for linting (no configuration file needed)
- Checks both source code and tests
- Must pass with "All checks passed!" message
- Configuration is minimal (project uses ruff defaults)

### Type Checking

**ALWAYS run before committing code changes:**

```bash
poetry run ty check meteostat/ tests/unit/ tests/integration/ tests/fixtures.py
```

- Uses `ty` type checker (not mypy or pyright)
- Checks source code and test files
- Must pass with "All checks passed!" message
- The project includes `py.typed` marker for type information

### Building the Package

To build distribution files:

```bash
poetry build
```

- Creates `dist/meteostat-{version}.tar.gz` (source distribution)
- Creates `dist/meteostat-{version}-py3-none-any.whl` (wheel)
- Build artifacts are in `.gitignore` (do not commit)

## Project Layout and Architecture

### Directory Structure

```
meteostat/
├── meteostat/             # Main package source code
│   ├── api/               # Public API (daily, hourly, monthly, normals, stations, etc.)
│   ├── core/              # Core utilities (cache, logger, network, validator)
│   ├── interpolation/     # Data interpolation (IDW, nearest, lapse rate)
│   ├── providers/         # Data provider implementations
│   ├── utils/             # Utilities (conversions, data, geo, parsers, validators)
│   ├── enumerations.py    # Enums (Granularity, Parameter, Provider, UnitSystem)
│   ├── parameters.py      # Parameter definitions
│   └── typing.py          # Type definitions (Station, License, etc.)
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration
│   ├── provider/          # Provider tests (nightly CI only)
│   └── fixtures/          # Shared test fixtures and data
├── examples/              # Example scripts (chart, hourly, daily, etc.)
├── .github/
│   └── workflows/         # CI workflows
├── pyproject.toml         # Poetry configuration and metadata
└── poetry.lock            # Locked dependencies
```

### Key Files

- **`pyproject.toml`**: Poetry configuration, dependencies, build settings
- **`meteostat/__init__.py`**: Public API exports
- **`meteostat/api/`**: Main user-facing API functions
- **`meteostat/providers/index.py`**: Provider registry mapping station IDs to providers

### Important Conventions

1. **Module exports**: Public API is explicitly defined in `__all__` in `__init__.py`
2. **Type annotations**: All code should have type annotations (checked by `ty`)
3. **Pandas DataFrames**: Most data is returned as pandas DataFrames with specific column names

## CI/CD Workflows

### GitHub Actions Workflows

The repository has multiple CI workflows (all in `.github/workflows/`):

1. **`tests.yml`** - Runs on push to main and all PRs
   - Runs unit and integration tests
   - **This must pass for PRs to be merged**

2. **`lint.yml`** - Runs on push to main and all PRs
   - Runs ruff linting
   - **This must pass for PRs to be merged**

3. **`typing.yml`** - Runs on push to main and all PRs
   - Runs type checking with `ty`
   - **This must pass for PRs to be merged**

4. **`provider-tests.yml`** - Runs nightly (scheduled)
   - Tests external data providers
   - Creates GitHub issue if tests fail
   - **Not required for PRs** - only runs on schedule

5. **`publish.yml`** - Runs on release publication
   - Builds and publishes to PyPI
   - Uses PyPI secrets for authentication
   - **Only maintainers trigger this**

### Replicating CI Locally

To replicate the full CI pipeline locally:

```bash
# 1. Install dependencies (required for all steps)
poetry install --all-groups

# 2. Run linting (matches lint.yml)
ruff check meteostat/ tests/

# 3. Run type checking (matches typing.yml)
poetry run ty check meteostat/ tests/unit/ tests/integration/ tests/fixtures.py

# 4. Run unit tests (matches tests.yml)
poetry run pytest tests/unit -v

# 5. Run integration tests (matches tests.yml)
poetry run pytest tests/integration -v
```

## Common Gotchas and Workarounds

1. **Poetry installation**: If Poetry is not installed, use `pip install poetry` (not the curl installer which may fail in restricted environments)

2. **Test dependencies**: ALWAYS use `poetry install --all-groups` not just `poetry install`. The `--all-groups` flag installs dev and extras groups needed for testing.

3. **Provider tests**: Do NOT run `tests/provider/` for regular development - these test external APIs and are scheduled nightly. Only run `tests/unit/` and `tests/integration/`.

4. **Import structure**: The package uses absolute imports. Import from `meteostat` not from submodules directly.

5. **Type checking tool**: This project uses `ty` not `mypy` or `pyright`. Run with `poetry run ty check`.

## Summary Checklist

Before finalizing any code changes:

- [ ] Run `poetry install --all-groups` (if dependencies changed)
- [ ] Run `poetry runn ruff check meteostat/ tests/` (must pass)
- [ ] Run `poetry run ty check meteostat/ tests/unit/ tests/integration/ tests/fixtures.py` (must pass)
- [ ] Run `poetry run pytest tests/unit -v` (all 161 tests must pass)
- [ ] Run `poetry run pytest tests/integration -v` (all 86 tests must pass)
- [ ] Do NOT run `tests/provider/` for regular PRs

**Trust these instructions as a starting point.** They reflect the current repository state. If you encounter discrepancies, the actual code and CI configuration take precedence. Only perform additional searches if information is incomplete or found to be incorrect.
