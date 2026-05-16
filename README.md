# Power Monitor — macOS Battery & Power Monitoring TUI ⚡🔋

[![PyPI](https://img.shields.io/pypi/v/powermonitor.svg)](https://pypi.org/project/powermonitor/)
[![Python](https://img.shields.io/pypi/pyversions/powermonitor.svg)](https://pypi.org/project/powermonitor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**powermonitor** is a lightweight **macOS battery monitor**, **MacBook charging monitor**, and **real-time power
usage TUI** for developers and power users. It displays live wattage, voltage, amperage, battery percentage, charger
details, historical charts, and battery health trends directly in your terminal.

Use it to answer questions like: “How many watts is my Mac using?”, “Is my charger negotiating the expected power?”,
and “How is my MacBook battery capacity changing over time?” 📈

**Package name:** `powermonitor` · **Command:** `powermonitor` · **Platform:** macOS · **Storage:** local SQLite

## Quick Start 🚀

```bash
uvx powermonitor
```

## Table of Contents

- [Why Power Monitor?](#why-power-monitor)
- [Common Use Cases](#common-use-cases)
- [Feature Overview](#feature-overview-)
- [Installation](#installation-)
- [Usage](#usage)
- [CLI Commands](#cli-commands)
  - [CLI Command Reference](#cli-command-reference)
- [Requirements](#requirements)
- [Architecture](#architecture)
- [Data and Privacy](#data-and-privacy-)
- [Development](#development)
- [Power Monitor vs Built-in macOS Tools](#power-monitor-vs-built-in-macos-tools-)
- [Performance](#performance)
- [FAQ](#faq-)
- [License](#license)

## Why Power Monitor?

- 🖥️ **Beautiful terminal dashboard** - Auto-updating Textual TUI with an adaptive 3-panel layout
- ⚡ **Real-time macOS power monitoring** - Refreshes every 1 second by default
- 📊 **Live electrical metrics** - Watts, negotiated charger power, voltage, amperage, and battery percentage
- 🔋 **MacBook battery tracking** - Capacity, charging state, AC power status, and charger information
- 📈 **Historical visualization** - Power chart and rolling statistics for recent readings
- 🏥 **Battery health analysis** - Track capacity changes and battery degradation over time
- 💾 **Local SQLite history** - Automatic background logging with safe resource management
- 📤 **CSV/JSON export** - Analyze macOS power data in spreadsheets, notebooks, or scripts
- 🎯 **IOKit/SMC collection** - Direct macOS API integration via `ctypes` where available
- 🔄 **Reliable fallback** - Gracefully falls back to `ioreg` subprocess collection
- ⚙️ **Configurable** - Optional TOML config file plus CLI overrides
- 🧹 **Easy cleanup** - Remove old readings by age or clear the local database

## Common Use Cases

- Monitor MacBook charging wattage and USB-C power adapter behavior ⚡
- Watch battery drain and power usage while developing, gaming, compiling, or video editing
- Export power readings for performance testing, battery experiments, or long-running benchmarks
- Inspect charger metadata and negotiated wattage without opening system settings
- Track battery capacity trends from the terminal over days or weeks

## Feature Overview ✨

| Need | powermonitor helps by |
| --- | --- |
| Real-time Mac power usage | Showing live watts, voltage, amperage, battery %, and charging state |
| Charger debugging | Displaying negotiated wattage, charger name, and manufacturer when macOS exposes them |
| Battery health tracking | Comparing capacity readings across days to reveal degradation trends |
| Repeatable experiments | Saving local SQLite history and exporting CSV/JSON data |
| Terminal-native workflow | Running as a fast Textual TUI or focused CLI commands |

## Installation 📦

Install the `powermonitor` command from PyPI with your preferred Python tool manager.

### Install with uv (recommended)

```bash
uv tool install powermonitor
```

### Run without installing

```bash
uvx powermonitor
```

### Install with pipx

```bash
pipx install powermonitor
```

### Install with pip

```bash
python -m pip install powermonitor
```

> `uv tool install` or `pipx install` is recommended for keeping the CLI isolated from project environments.

## Usage

### Launch the TUI

```bash
# Launch auto-updating TUI with default settings
powermonitor

# Customize TUI settings
powermonitor --interval 1.0 --stats-limit 100 --chart-limit 60

# Enable debug logging
powermonitor --debug
```

**TUI Options:**

- `--interval` / `-i` - Data collection interval in seconds (default: 1.0)
- `--stats-limit` - Number of readings for statistics (default: 100)
- `--chart-limit` - Number of readings in chart (default: 60)
- `--debug` - Enable debug logging

The TUI displays live power data, rolling statistics, and a compact power chart. The layout adapts to the terminal size.
Tall terminals stack the live data, statistics, and chart panels vertically.
Shorter wide terminals place the live and statistics panels side by side above the chart, while narrow terminals avoid
squeezing those summary panels into unreadable columns.

```
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

**Keyboard Controls:**

- `q` or `ESC` - Quit application
- `r` - Force refresh data
- `c` - Clear history (with confirmation)

### Configuration File

powermonitor supports an optional configuration file at `~/.powermonitor/config.toml`:

```toml
# powermonitor configuration file

[tui]
interval = 1.0           # Data collection interval in seconds
stats_limit = 100        # Number of readings for statistics
chart_limit = 60         # Number of readings to display in chart

[database]
path = "~/.powermonitor/powermonitor.db"  # Database file location

[cli]
default_history_limit = 20           # Default limit for history command
default_export_limit = 1000          # Default limit for export command

[logging]
level = "INFO"           # Logging level: DEBUG, INFO, WARNING, ERROR
```

**Configuration Priority**: CLI arguments > Config file > Defaults

If no config file exists, powermonitor uses sensible defaults. CLI arguments always override config file values.

Manage the config file without launching the TUI:

```bash
# Create ~/.powermonitor/config.toml if it does not already exist
powermonitor config init

# Show the effective config and config file path
powermonitor config show

# Validate config syntax, sections, keys, and values
powermonitor config validate
```

`powermonitor config init` refuses to overwrite an existing file.

**Example**: Set custom database path and collection interval:

```toml
[database]
path = "~/Documents/power-data.db"

[tui]
interval = 2.0
```

Then run: `powermonitor` (uses config) or `powermonitor --interval 0.5` (overrides config)

## CLI Commands

### CLI Command Reference

| Command | What it does |
| --- | --- |
| `powermonitor` | Launches the real-time Textual dashboard |
| `powermonitor export OUTPUT` | Exports saved readings as CSV or JSON |
| `powermonitor stats` | Shows database count, date range, size, and path |
| `powermonitor history` | Prints recent power readings in a table |
| `powermonitor health` | Summarizes battery capacity changes over time |
| `powermonitor cleanup` | Deletes old readings or clears the local database |
| `powermonitor config` | Creates, shows, and validates `config.toml` |

### Manage Configuration

Create, inspect, and validate `~/.powermonitor/config.toml`:

```bash
powermonitor config init
powermonitor config show
powermonitor config validate
```

### Export Data

Export power readings to CSV or JSON format:

```bash
# Export to CSV (auto-detected from extension)
powermonitor export data.csv

# Export to JSON
powermonitor export data.json

# Export last 1000 readings
powermonitor export data.csv --limit 1000

# Manually specify format
powermonitor export backup.txt --format csv
```

### Database Statistics

Show database information and statistics:

```bash
powermonitor stats
```

Output:
```
Database Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total readings       12,450
Earliest reading     2025-12-01 10:30:00
Latest reading       2026-01-06 15:22:00
Database size        2.4 MB
Database path        /Users/you/.powermonitor/powermonitor.db
```

### View History

Display recent power readings in a formatted table:

```bash
# Show last 20 readings (default)
powermonitor history

# Show last 50 readings
powermonitor history --limit 50
```

Output shows time, power, battery %, voltage, current, and status.

### Clean Up Data

Remove old readings to manage database size:

```bash
# Delete readings older than 30 days
powermonitor cleanup --days 30

# Delete all readings (requires confirmation)
powermonitor cleanup --all
```

### Battery Health

Track battery degradation over time:

```bash
# Analyze last 30 days (default)
powermonitor health

# Analyze last 60 days
powermonitor health --days 60
```

Output:
```
Battery Health Analysis (30 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
First reading        2025-12-06
First avg capacity   4,709 mAh
Last reading         2026-01-06
Last avg capacity    4,650 mAh
Change               -59 mAh (-1.25%)
Status               ⚠️  Degrading (normal wear)
Days analyzed        30
```

## Requirements

- **macOS**: 12.0+ (Monterey or later)
- **Python**: 3.13+ (uses modern type hints)
- **Dependencies**: Textual, Rich, textual-plotext, Typer, Peewee, and Loguru (installed automatically)
- **Permissions**: no root privileges required; exact sensor availability can vary by Mac model

## Architecture

### Adaptive TUI Layout (3 Panels)

The TUI keeps the same three widgets across layout changes and chooses the most readable arrangement from the current
terminal size.

1. **LiveDataPanel** (green) - Real-time power data
   - Status: ⚡ Charging / 🔌 AC Power / 🔋 On Battery
   - Power: watts_actual / watts_negotiated
   - Battery: percentage, capacity (mAh)
   - Electrical: voltage, amperage
   - Charger info (if available)

2. **StatsPanel** (cyan) - Historical statistics
   - Time range (earliest/latest)
   - Average/min/max power
   - Average battery percentage
   - Based on last 100 readings

3. **ChartWidget** (blue) - Power over time
   - Line chart with 60 data points
   - Shows actual power and max negotiated power
   - Auto-scales based on data

### Data Collection

powermonitor uses two collectors with automatic fallback:

1. **IOKitCollector** (preferred) - Direct IOKit/SMC API via ctypes
   - Reads 7 SMC sensors: PPBR, PDTR, PSTR, PHPC, PDBR, TB0T, CHCC
   - Most accurate power readings (PDTR sensor)
   - Zero overhead (no subprocess)

2. **IORegCollector** (fallback) - Subprocess-based
   - Executes `ioreg -rw0 -c AppleSmartBattery -a`
   - Parses plist output using Python's plistlib
   - Works on all Macs without special permissions

### Database

All readings automatically saved to SQLite with proper resource management:

**Default location**: `~/.powermonitor/powermonitor.db`

**Custom location** (via config file):
```toml
[database]
path = "/path/to/custom.db"
```

**Resource Management**:
- Automatic connection cleanup using context managers
- No ResourceWarnings or connection leaks
- Proper transaction handling for all write operations
- Safe shutdown and cleanup in TUI mode

**Schema**:
```sql
CREATE TABLE power_readings (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    watts_actual REAL,
    watts_negotiated INTEGER,
    voltage REAL,
    amperage REAL,
    current_capacity INTEGER,
    max_capacity INTEGER,
    battery_percent INTEGER,
    is_charging INTEGER,
    external_connected INTEGER,
    charger_name TEXT,
    charger_manufacturer TEXT
);
```

## Data and Privacy 🔐

- Power readings are stored locally in SQLite at `~/.powermonitor/powermonitor.db` by default.
- `powermonitor` does not require a cloud account or background service.
- Data leaves your machine only when you explicitly export it with `powermonitor export`.
- Database cleanup is manual and explicit via `powermonitor cleanup`.

## Project Structure

```
powermonitor/
├── pyproject.toml              # uv project config
├── uv.lock                     # Dependency lock file
├── src/
│   └── powermonitor/
│       ├── cli.py              # Entry point
│       ├── models.py           # PowerReading dataclass
│       ├── database.py         # SQLite operations
│       ├── config.py           # PowerMonitorConfig dataclass
│       ├── config_loader.py    # TOML config file loader
│       ├── logger.py           # Logging configuration
│       ├── collector/          # Data collection
│       │   ├── base.py         # PowerCollector protocol
│       │   ├── ioreg.py        # Subprocess collector
│       │   ├── factory.py      # Auto-fallback logic
│       │   └── iokit/          # IOKit/SMC FFI
│       │       ├── bindings.py # ctypes bindings
│       │       ├── structures.py # SMC data structures
│       │       ├── parser.py   # Binary parsing
│       │       ├── connection.py # SMCConnection
│       │       └── collector.py # IOKitCollector
│       └── tui/                # Textual TUI
│           ├── app.py          # PowerMonitorApp
│           └── widgets.py      # Custom widgets
└── tests/
    └── fixtures/               # Test data
```

## Development

### Setup

```bash
uv sync
```

### Quality Checks

```bash
make format   # Format with Ruff
make lint     # Run Ruff checks
make type     # Run ty type checking
make test     # Run pytest with coverage
make all      # Run format, lint, type check, and tests
```

### Manual Testing

```bash
uv run powermonitor
```

### Collector Debugging

```bash
# Test one data collection pass
uv run python - <<'PY'
from powermonitor.collector import default_collector

print(default_collector().collect())
PY

# Show verbose collector selection and fallback details
uv run python - <<'PY'
from powermonitor.collector import default_collector

collector = default_collector(verbose=True)
print(collector.collect())
PY
```

### Build

```bash
uv build --no-sources
```

## Power Monitor vs Built-in macOS Tools 🧰

macOS includes tools like `ioreg`, `pmset`, Activity Monitor, and System Information, but they are not optimized for a
continuous terminal dashboard. `powermonitor` combines live power metrics, battery status, charger details, history,
charts, and export commands in one developer-friendly CLI.

## Performance

- **Memory**: <50MB RAM
- **CPU**: <1% when idle
- **Update interval**: 1 second (configurable)
- **Database**: Indexed for fast queries

## FAQ ❓

### What is powermonitor?

`powermonitor` is a Python CLI and terminal UI for macOS power monitoring. It shows real-time Mac battery status,
wattage, voltage, amperage, charger information, historical charts, and battery health data.

### Does it work on Apple Silicon and Intel Macs?

It is designed for macOS and uses IOKit/SMC data when available, with an `ioreg` fallback for broad compatibility.
The exact sensors exposed can vary by Mac model and macOS version.

### Where is the power history stored?

Readings are stored locally in SQLite at `~/.powermonitor/powermonitor.db` by default. You can change the database path
in `~/.powermonitor/config.toml`.

### Can I export MacBook battery and charging data?

Yes. Use `powermonitor export data.csv` or `powermonitor export data.json` to export historical power readings for
spreadsheets, notebooks, scripts, and benchmark reports.

## Recent Improvements

- ✅ **Resource Management**: Proper SQLite connection cleanup eliminates ResourceWarnings
- ✅ **Configuration System**: TOML-based config with 3-layer priority (CLI > Config > Defaults)
- ✅ **CLI Commands**: Export, stats, history, cleanup, and battery health tracking
- ✅ **Code Quality**: Clean test infrastructure with proper fixture cleanup
- ✅ **Database Operations**: Context manager pattern for all database operations

## Migration Notes

- **To**: Python TUI with unified auto-updating interface
- **Reason**: Better rapid development, easier maintenance, similar performance for 2s intervals
- **Preserved**: All data collection logic, database schema, SMC sensor access (via ctypes)
- **Breaking Change**: `POWERMONITOR_DB_PATH` environment variable removed (use config.toml instead)

## License

MIT
