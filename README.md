# powermonitor: macOS Battery Monitor & MacBook Power Usage TUI ⚡🔋

[![PyPI](https://img.shields.io/pypi/v/powermonitor.svg)](https://pypi.org/project/powermonitor/)
[![Python](https://img.shields.io/pypi/pyversions/powermonitor.svg)](https://pypi.org/project/powermonitor/)
[![CI](https://github.com/narumiruna/power-monitor/actions/workflows/python.yml/badge.svg)](https://github.com/narumiruna/power-monitor/actions/workflows/python.yml)
[![Docs](https://github.com/narumiruna/power-monitor/actions/workflows/docs.yml/badge.svg)](https://github.com/narumiruna/power-monitor/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**powermonitor** is an open-source **macOS battery monitor**, **MacBook charging wattage checker**, and **real-time terminal power usage dashboard**. It shows live watts, voltage, amperage, battery percentage, charging state, charger details, historical charts, SQLite history, battery health trends, and CSV/JSON export.

Use it when you want a terminal-native alternative to repeatedly checking Activity Monitor, System Information, `pmset`, or raw `ioreg` output.

**Package:** `powermonitor` · **Command:** `powermonitor` · **Platform:** macOS · **Docs:** <https://narumiruna.github.io/power-monitor/>

## Quick start

Run the Mac power monitor without installing a persistent tool:

```bash
uvx powermonitor
```

Or install the command as an isolated tool:

```bash
uv tool install powermonitor
powermonitor
```

## Why use powermonitor?

- ⚡ **Real-time MacBook wattage**: live actual power draw and negotiated charger watts.
- 🔋 **Battery status at a glance**: battery percentage, capacity, charging state, and AC power state.
- 🔌 **USB-C and MagSafe charger diagnostics**: charger name, manufacturer, and negotiated power when macOS exposes them.
- 📈 **Terminal charts**: rolling Textual dashboard for recent power usage.
- 🏥 **Battery health trend**: summarize maximum capacity changes over days or weeks.
- 💾 **Local SQLite history**: automatic logging under `~/.powermonitor/` by default.
- 📤 **CSV/JSON export**: analyze MacBook battery and charging data in spreadsheets, notebooks, or scripts.
- 🧰 **Scriptable CLI**: history, stats, health, export, cleanup, and config commands.
- 🔄 **Reliable macOS collection**: direct IOKit/SMC integration with an `ioreg` fallback.

## Common use cases

- Check whether a USB-C charger, cable, dock, or power bank is delivering expected wattage.
- Watch battery drain while compiling, gaming, rendering video, or running benchmarks.
- Compare MacBook power usage before and after changing apps, settings, or peripherals.
- Export power readings for performance reports or battery experiments.
- Track battery capacity trends without a cloud account or background service.

## Feature overview

| Need | powermonitor helps by |
| --- | --- |
| Real-time macOS power monitoring | Showing live watts, voltage, amperage, battery %, and charging state |
| Charger debugging | Displaying negotiated wattage, charger name, and manufacturer when available |
| Battery health tracking | Comparing capacity readings across days to reveal degradation trends |
| Repeatable experiments | Saving local SQLite history and exporting CSV/JSON data |
| Terminal-native workflow | Running as a responsive Textual TUI or focused CLI commands |
| Broad Mac compatibility | Trying IOKit/SMC first, then falling back to `ioreg` collection |

## Installation

### uv (recommended)

```bash
uv tool install powermonitor
```

### Run without installing

```bash
uvx powermonitor
```

### pipx

```bash
pipx install powermonitor
```

### pip

```bash
python -m pip install powermonitor
```

`uv tool install` or `pipx install` keeps the CLI isolated from project environments.

## Usage

### Launch the real-time TUI

```bash
powermonitor
```

Useful launch options:

```bash
powermonitor --interval 2.0
powermonitor --stats-limit 200 --chart-limit 120
powermonitor --debug
```

| Option | Purpose | Default |
| --- | --- | --- |
| `--interval`, `-i` | Data collection interval in seconds | `1.0` |
| `--stats-limit` | Number of readings used for rolling statistics | `100` |
| `--chart-limit` | Number of readings shown in the chart | `60` |
| `--debug` | Enable debug logging | `false` |

Keyboard controls: `q` or `Esc` quits, `r` refreshes, and `c` clears history after confirmation.

```text
┌─ powermonitor ──────────────────────────────┐
│ Real-Time Power       │ Statistics         │
│ ⚡ 45.2W / 67W         │ Last 100 readings  │
│ 🔋 72%  20.0V × 2.26A │ Avg: 42.3W         │
├───────────────────────────────────────────┤
│ Power Chart (Last 60 readings)            │
│     55W ┤      ╭──╮                       │
│     45W ┤  ╭───╯  ╰──╮                    │
│     35W ┤──╯         ╰─                   │
│         └───────────────────               │
│ [q] Quit  [r] Refresh  [c] Clear History │
└───────────────────────────────────────────┘
```

The dashboard adapts to terminal size: tall terminals stack panels vertically, short wide terminals place summary panels side by side, and narrow terminals avoid unreadable columns.

## CLI command reference

| Command | What it does |
| --- | --- |
| `powermonitor` | Launch the real-time Textual dashboard |
| `powermonitor history` | Show recent saved readings |
| `powermonitor stats` | Show database count, date range, size, and path |
| `powermonitor health` | Summarize battery capacity changes over time |
| `powermonitor export OUTPUT` | Export readings as CSV or JSON |
| `powermonitor cleanup` | Delete old readings or clear the database |
| `powermonitor config` | Create, inspect, and validate `config.toml` |

### Export MacBook battery data

```bash
powermonitor export data.csv
powermonitor export data.json
powermonitor export data.csv --limit 1000
powermonitor export backup.txt --format csv
```

### View history and stats

```bash
powermonitor history
powermonitor history --limit 50
powermonitor stats
```

### Analyze battery health

```bash
powermonitor health
powermonitor health --days 60
```

### Clean up local data

```bash
powermonitor cleanup --days 30
powermonitor cleanup --all
```

## Configuration

powermonitor uses sensible defaults and supports an optional config file at `~/.powermonitor/config.toml`.

```bash
powermonitor config init
powermonitor config show
powermonitor config validate
```

Example config:

```toml
[tui]
interval = 1.0
stats_limit = 100
chart_limit = 60

[database]
path = "~/.powermonitor/powermonitor.db"

[cli]
default_history_limit = 20
default_export_limit = 1000

[logging]
level = "INFO"
```

Configuration priority: **CLI arguments > config file > defaults**.

## Requirements

- macOS 12.0+ Monterey or later
- Python 3.13+
- No root privileges required

Sensor availability varies by Mac model, charger, cable, dock, and macOS version. powermonitor records the values macOS exposes.

## Data and privacy

- Readings are stored locally in SQLite at `~/.powermonitor/powermonitor.db` by default.
- No cloud account, telemetry service, or daemon is required.
- Data leaves your machine only when you explicitly export it with `powermonitor export`.
- Cleanup is manual via `powermonitor cleanup`.

## Architecture

powermonitor keeps collection, storage, CLI, and UI concerns separate:

```text
macOS power APIs
  ├─ IOKit/SMC collector (preferred)
  └─ ioreg collector (fallback)
          ↓
PowerReading dataclass
          ↓
SQLite database + live Textual widgets
          ↓
CLI history, stats, health, cleanup, and export commands
```

Core modules live under `src/powermonitor/`:

- `cli.py`: Typer CLI entry point and subcommands.
- `collector/`: IOKit/SMC and `ioreg` data collection.
- `database.py`: SQLite persistence.
- `config.py` and `config_loader.py`: validated TOML configuration.
- `tui/`: Textual application, widgets, and adaptive layout.

## Documentation

Full documentation is available at <https://narumiruna.github.io/power-monitor/>:

- [Installation](https://narumiruna.github.io/power-monitor/installation/)
- [TUI usage](https://narumiruna.github.io/power-monitor/usage/)
- [CLI commands](https://narumiruna.github.io/power-monitor/commands/)
- [Configuration](https://narumiruna.github.io/power-monitor/configuration/)
- [Data and privacy](https://narumiruna.github.io/power-monitor/data-and-privacy/)
- [Architecture](https://narumiruna.github.io/power-monitor/architecture/)

## Power Monitor vs built-in macOS tools

macOS includes Activity Monitor, System Information, `pmset`, and `ioreg`, but they are not optimized for continuous terminal monitoring. powermonitor combines live power metrics, MacBook battery status, charger details, SQLite history, charts, health summaries, cleanup, and exports in one developer-friendly CLI.

## FAQ

### What is powermonitor?

powermonitor is a Python CLI and terminal UI for macOS power monitoring. It shows real-time MacBook wattage, battery status, voltage, amperage, charger information, history, charts, and battery health data.

### Does it work on Apple Silicon and Intel Macs?

It is designed for macOS and uses IOKit/SMC data when available, with an `ioreg` fallback for broad compatibility. Exact sensors can vary by Mac model and macOS version.

### Can powermonitor show USB-C charger wattage?

Yes, when macOS exposes the information. powermonitor displays negotiated charger watts, charger name, and manufacturer when available.

### Where is power history stored?

By default, readings are stored locally in SQLite at `~/.powermonitor/powermonitor.db`. You can change the path in `~/.powermonitor/config.toml`.

### Can I export MacBook charging and battery data?

Yes. Use `powermonitor export data.csv` or `powermonitor export data.json`.

## Development

```bash
uv sync
make format
make lint
make type
make test
make all
```

Build release artifacts:

```bash
uv build --no-sources
```

Build the MkDocs website locally:

```bash
uv sync --group docs
uv run mkdocs serve
uv run mkdocs build --strict
```

## License

MIT
