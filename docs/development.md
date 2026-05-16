---
title: Development
summary: Set up powermonitor for local development, run quality checks, build docs, and build release artifacts.
description: Development guide for powermonitor, including uv setup, Ruff, ty, pytest, MkDocs documentation commands, project structure, and release build checks.
---

# Development

This project uses Python 3.13+, `uv`, `just`, Ruff, ty, pytest, and MkDocs.

Install `just` if your system does not already provide it. On macOS, use `brew install just`. Run `just` or `just --list` to see available recipes.

## Set up the repository

```bash
git clone https://github.com/narumiruna/power-monitor.git
cd power-monitor
uv sync
```

Run the local command:

```bash
uv run powermonitor --help
uv run powermonitor
```

The TUI only runs on macOS.

## Quality checks

Use the repository `justfile`:

```bash
just --list   # Show available recipes
just format   # Ruff formatter
just lint     # Ruff checks with autofix
just type     # ty type checker
just test     # pytest with coverage
just all      # format, lint, type, test
```

## Documentation site

Install docs dependencies and serve the MkDocs site locally:

```bash
uv sync --group docs
uv run mkdocs serve
```

Build the static site with strict validation:

```bash
uv run mkdocs build --strict
```

The GitHub Actions workflow in `.github/workflows/docs.yml` builds documentation on pull requests and deploys GitHub Pages from `main` or manual dispatch.

## Project structure

```text
powermonitor/
├── .github/workflows/       # CI, release, publish, and docs workflows
├── docs/                    # MkDocs content
├── src/powermonitor/        # Package source
├── tests/                   # pytest suite and fixtures
├── mkdocs.yml               # Documentation site config
├── pyproject.toml           # Package metadata and tool config
└── uv.lock                  # Locked dependencies
```

## Build artifacts

Build release artifacts without local source overrides:

```bash
uv build --no-sources
```

Before publishing, verify tests and inspect the built wheel/sdist contents.

## Documentation guidelines

- Keep README content concise and keyword-rich for GitHub and PyPI discovery.
- Put detailed user guides in `docs/`.
- Keep command examples aligned with `uv run powermonitor --help` and `uv run powermonitor COMMAND --help`.
- Prefer local, reproducible examples over live macOS sensor assumptions when writing tests.
