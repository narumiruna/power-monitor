# Power Monitor

macOS power monitoring tool with auto-updating TUI for real-time battery and charging status.

## Quick Start

```bash
uvx powermonitor
```

## Features

- 🖥️ **Auto-updating TUI** with 3-panel layout (Textual framework)
- ⚡ **Real-time monitoring** - Updates every 1 second automatically
- 📊 **Live power metrics** - Voltage, amperage, wattage, battery %
- 📈 **Historical visualization** - Power chart and statistics
- 🔋 **Battery tracking** - Capacity, charging status, charger info
- 💾 **SQLite persistence** - Automatic background data logging with proper resource management
- 🎯 **IOKit/SMC access** - Direct macOS API integration via ctypes
- 🔄 **Auto-fallback** - Graceful fallback to subprocess-based collection
- ⚙️ **Configuration file** - Optional TOML config with CLI override support
- 📤 **Data export** - Export to CSV/JSON formats
- 🧹 **Data cleanup** - Remove old readings by age or clear all
- 🏥 **Battery health** - Track battery degradation over time

## Installation

### Install with uv (recommended)

```bash
uv tool install powermonitor
```

### Install with pipx

```bash
pipx install powermonitor
```

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

The TUI displays:

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

### CLI Commands

#### Manage Configuration

Create, inspect, and validate `~/.powermonitor/config.toml`:

```bash
powermonitor config init
powermonitor config show
powermonitor config validate
```

#### Export Data

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

#### Database Statistics

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

#### View History

Display recent power readings in a formatted table:

```bash
# Show last 20 readings (default)
powermonitor history

# Show last 50 readings
powermonitor history --limit 50
```

Output shows time, power, battery %, voltage, current, and status.

#### Clean Up Data

Remove old readings to manage database size:

```bash
# Delete readings older than 30 days
powermonitor cleanup --days 30

# Delete all readings (requires confirmation)
powermonitor cleanup --all
```

#### Battery Health

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

### Development Mode

```bash
# Run with verbose collector info
uv run python -c "from powermonitor.collector import default_collector; collector = default_collector(verbose=True); print(collector.collect())"

# Test data collection
uv run python -c "from powermonitor.collector import default_collector; print(default_collector().collect())"
```

## Requirements

- **macOS**: 12.0+ (Monterey or later)
- **Python**: 3.13+ (uses modern type hints)
- **Dependencies**: textual, rich, textual-plotext (auto-installed by uv)

## Architecture

### TUI Layout (3 Panels)

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

### Code Quality

```bash
# Type checking
uv run ty check .

# Linting
uv run ruff check src/

# Auto-formatting
uv run ruff format src/

# Run all checks
uv run ty check . && uv run ruff check src/ && uv run ruff format src/
```

### Testing

```bash
# Run tests (when available)
uv run pytest

# Manual testing
uv run powermonitor
```

## Performance

- **Memory**: <50MB RAM
- **CPU**: <1% when idle
- **Update interval**: 1 second (configurable)
- **Database**: Indexed for fast queries

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
