# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Fixed wheel packaging so joke sound assets are included from `trushell/sounds/`.
- Updated README custom sound instructions to use the current `trushell/sounds/` path.
- Replaced a one-off Rich console print in `cli.py` with `typer.echo()`.
- Added double-checked database initialization to avoid taking the initialization lock after startup.

## 0.1.0 - Initial release

- Reorganized the repository into a proper Python package.
- Added a modern `pyproject.toml` and Hatchling packaging.
- Added user directory storage for SQLite and JSON app state.
- Added robust CLI entrypoint and Typer integration.
- Added documentation, tests, and GitHub CI.
