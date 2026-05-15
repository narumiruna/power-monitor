# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.13+ package using a `src/` layout. Core code lives in `src/powermonitor/`:

- `src/powermonitor/cli.py`: Typer CLI entry point and command wiring.
- `src/powermonitor/tui/`: Textual TUI application and widgets.
- `src/powermonitor/collector/`: power data collection strategies, including IOKit and `ioreg` fallback collectors.
- `src/powermonitor/database.py`, `config.py`, `config_loader.py`: persistence and configuration support.
- `tests/`: pytest suite, with fixtures under `tests/fixtures/`.

Keep new modules near the feature they support; add shared helpers only for real duplication.

## Build, Test, and Development Commands

- `uv sync`: install locked dependencies.
- `uv run powermonitor`: run the local CLI/TUI.
- `make format`: format the project with Ruff.
- `make lint`: run Ruff checks with autofix enabled.
- `make type`: run `ty check .`.
- `make test`: run pytest with coverage.
- `make all`: run format, lint, type check, and tests.
- `uv build --no-sources`: build release artifacts without local source overrides.

Use `uv run ...` unless a `Makefile` target already wraps the command.

## Coding Style & Naming Conventions

Ruff is the formatter and linter. Line length is 120 characters, imports are sorted as single-line imports, and lint rules cover pycodestyle, pyflakes, pep8-naming, pyupgrade, bugbear, comprehensions, and simplify checks. This package ships `py.typed`, so keep public APIs type-checkable.

Use `snake_case` for functions, methods, variables, and modules; use `PascalCase` for classes and dataclasses. Keep CLI options consistent with existing Typer commands.

## Testing Guidelines

Tests use pytest with coverage configured in `pyproject.toml`. Name files `test_*.py`, classes `Test*`, and functions `test_*`. Put deterministic sample data in `tests/fixtures/`; avoid depending on live macOS power state when a fixture or mock can cover the behavior.

Run `make test` for behavior changes and `make all` for broader changes.

## Commit & Pull Request Guidelines

Recent history uses short, imperative commit subjects such as `Use connection_context() for all database operations`. Keep commits focused on one intent. Stage only intended paths; do not use blanket staging such as `git add -A`.

Pull requests should include a concise behavior summary, tests run, and any macOS-specific assumptions. For TUI changes, include screenshots or a short terminal recording when the visual behavior changes.

## Security & Configuration Tips

The app reads optional config from `~/.powermonitor/config.toml` and writes SQLite data under `~/.powermonitor/` by default. Do not commit local databases, exported personal power logs, or machine-specific config.
