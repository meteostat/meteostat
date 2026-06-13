## Repository

- https://github.com/meteostat/meteostat
- Use `gh` CLI to access issues, workflows, and more
- Use Conventional Commits (ONLY `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, `test` types allowed)

## Documentation

- https://github.com/meteostat/docs
- Use Context7 MCP server (library: `dev_meteostat_net`) for documentation beyond the codebase

## Testing

- Use `pytest` for testing
- Test levels:
  - Unit tests: Individual functions and methods (mocked dependencies & data)
  - Integration tests: Interactions between components (mocked data)
  - Provider tests: Chronological data fetching to ensure compatibility with external APIs (real data)
- EVERY provider MUST have a corresponding provider test