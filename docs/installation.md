---
title: Install powermonitor
summary: Install the powermonitor macOS battery monitor with uv, uvx, pipx, or pip.
description: Installation guide for powermonitor, a macOS battery monitor and MacBook power usage CLI, including uv, uvx, pipx, pip, upgrades, and requirements.
---

# Installation

powermonitor is published as the `powermonitor` Python package and provides the `powermonitor` command.

## Requirements

- **Operating system:** macOS 12.0+ Monterey or later
- **Python:** 3.13+
- **Permissions:** no root privileges required
- **Storage:** local SQLite database under `~/.powermonitor/` by default

!!! note
    powermonitor is macOS-only because it reads Mac power and battery data through IOKit/SMC or `ioreg`.

## Recommended: install with uv

Install the command as an isolated tool:

```bash
uv tool install powermonitor
powermonitor
```

Upgrade later with:

```bash
uv tool upgrade powermonitor
```

## Run without installing

Use `uvx` for one-off runs:

```bash
uvx powermonitor
```

This is the fastest way to try the real-time MacBook power monitor without changing a project environment.

## Install with pipx

```bash
pipx install powermonitor
powermonitor
```

Upgrade later with:

```bash
pipx upgrade powermonitor
```

## Install with pip

```bash
python -m pip install powermonitor
```

Prefer `uv tool install` or `pipx install` when you want to keep the CLI isolated from project dependencies.

## Verify the command

```bash
powermonitor --help
powermonitor config show
```

`powermonitor` without a subcommand launches the Textual TUI. On non-macOS platforms the command exits because the collector depends on macOS power APIs.

## Local development install

From a repository checkout:

```bash
git clone https://github.com/narumiruna/power-monitor.git
cd power-monitor
uv sync
uv run powermonitor --help
```

Build the package locally with:

```bash
uv build --no-sources
```

For documentation work, install the docs dependency group:

```bash
uv sync --group docs
uv run mkdocs serve
```
