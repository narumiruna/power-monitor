---
title: powermonitor
summary: macOS battery monitor and MacBook power usage TUI for charging wattage, battery health, and local power history.
description: powermonitor is a macOS battery monitor, MacBook charging wattage checker, and real-time terminal power usage dashboard with SQLite history and CSV/JSON export.
---

# powermonitor: macOS Battery Monitor & Power Usage TUI

**powermonitor** is an open-source **macOS battery monitor**, **MacBook power monitor**, and **terminal power usage dashboard**. It shows live wattage, voltage, amperage, battery percentage, charging state, charger metadata, historical power charts, and battery health trends directly in your terminal.

Use powermonitor when you want to answer practical Mac power questions:

- How many watts is my MacBook using right now?
- Is my USB-C or MagSafe charger negotiating the expected wattage?
- How fast does this workload drain the battery?
- How is maximum battery capacity changing over days or weeks?
- Can I export MacBook battery and charging data for analysis?

## Quick start

Run the real-time Textual TUI without installing a persistent tool:

```bash
uvx powermonitor
```

Or install it as an isolated command:

```bash
uv tool install powermonitor
powermonitor
```

See [Installation](installation.md) for `pipx`, `pip`, upgrade, and local development options.

## Feature highlights

| Need | powermonitor provides |
| --- | --- |
| Real-time Mac power usage | Live watts, voltage, amperage, battery percentage, and charging state |
| Charger diagnostics | Negotiated wattage, charger name, and manufacturer when macOS exposes them |
| Battery health tracking | Capacity trend summaries over a configurable number of days |
| Long-running experiments | Local SQLite logging plus CSV/JSON export |
| Terminal workflow | A responsive Textual TUI and scriptable CLI commands |
| Broad macOS collection | Direct IOKit/SMC collection with automatic `ioreg` fallback |

## Common use cases

- Monitor MacBook charging wattage while testing USB-C docks, cables, and power adapters.
- Watch power draw during builds, benchmarks, video editing, gaming, or model inference.
- Compare battery drain before and after changing apps, settings, or peripherals.
- Export power readings to spreadsheets, notebooks, or performance reports.
- Keep a local history of battery capacity and charging behavior without a cloud service.

## CLI overview

| Command | Purpose |
| --- | --- |
| `powermonitor` | Launch the real-time Textual dashboard |
| `powermonitor history` | Show recent saved power readings |
| `powermonitor stats` | Show SQLite database count, date range, size, and path |
| `powermonitor health` | Summarize battery capacity changes over time |
| `powermonitor export OUTPUT` | Export readings as CSV or JSON |
| `powermonitor cleanup` | Delete old readings or clear the database |
| `powermonitor config` | Create, inspect, and validate `config.toml` |

Read the full [CLI command reference](commands.md).

## Why not just use built-in macOS tools?

macOS already includes Activity Monitor, System Information, `pmset`, and `ioreg`. powermonitor combines the parts power users usually need from those tools into one terminal-native workflow: live wattage, charger details, battery percentage, history, charts, cleanup, and exports.

## Requirements

- macOS 12.0+ Monterey or later
- Python 3.13+
- No root privileges required

Sensor availability can vary by Mac model and macOS version. powermonitor prefers direct IOKit/SMC readings and falls back to `ioreg` when direct collection is unavailable.

## Data and privacy

Power readings are stored locally in SQLite at `~/.powermonitor/powermonitor.db` by default. Data leaves your machine only when you explicitly export it. See [Data and Privacy](data-and-privacy.md).

## Project links

- [GitHub repository](https://github.com/narumiruna/power-monitor)
- [PyPI package](https://pypi.org/project/powermonitor/)
- [Issue tracker](https://github.com/narumiruna/power-monitor/issues)
