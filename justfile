# Local task runner for powermonitor.
#
# Run `just` or `just --list` to discover recipes.
# Recipes intentionally preserve the previous task names so existing muscle memory
# can switch to `just <recipe>` with minimal friction.
# All Python tooling is invoked through `uv run` to use the locked project environment.
#
# Recipe descriptions use explicit `[doc(...)]` attributes. Plain `#` comments
# are kept for maintainers and do not have to double as CLI help text.

# Keep the default recipe private so `just --list` shows only actionable tasks.
[private]
default:
    @just --list --unsorted

[doc('Format Python source, tests, and tooling files with Ruff')]
format:
    uv run ruff format .

[doc('Run Ruff lint checks and apply safe autofixes')]
lint:
    uv run ruff check --fix .

[doc('Run ty type checking across the repository')]
type:
    uv run ty check .

[doc('Run the pytest suite with verbose output and coverage for src/')]
test:
    uv run pytest -v -s --cov=src tests

[doc('Build and upload a wheel to the configured Python package index')]
publish:
    uv build -f wheel
    uv publish

[doc('Run the full local quality gate used before larger changes')]
all: format lint type test
