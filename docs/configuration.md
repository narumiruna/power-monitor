---
title: Configure powermonitor
summary: Configure powermonitor with ~/.powermonitor/config.toml and CLI overrides.
description: Configuration guide for powermonitor, including TOML options for TUI refresh interval, SQLite database path, command defaults, logging, and validation.
---

# Configuration

powermonitor works without a config file, but you can create `~/.powermonitor/config.toml` to customize the TUI, SQLite database path, CLI defaults, and logging level.

## Create a default config

```bash
powermonitor config init
```

The command creates a commented config file and refuses to overwrite an existing file.

## Show the effective config

```bash
powermonitor config show
```

This prints the config file path, whether the file exists, the database path, and the effective values after defaults are applied.

## Validate the config file

```bash
powermonitor config validate
```

Validation checks TOML syntax, supported sections, supported keys, and value ranges before you launch the TUI.

## Config file format

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
level = "INFO"           # DEBUG, INFO, WARNING, or ERROR
```

## Precedence

Configuration priority is:

1. CLI arguments
2. `~/.powermonitor/config.toml`
3. Built-in defaults

For example, `powermonitor --interval 0.5` overrides `[tui].interval` for that run only.

## Common examples

### Store data in Documents

```toml
[database]
path = "~/Documents/powermonitor.db"
```

### Collect every two seconds

```toml
[tui]
interval = 2.0
```

### Keep larger default command windows

```toml
[cli]
default_history_limit = 100
default_export_limit = 10000
```

### Enable debug logs by default

```toml
[logging]
level = "DEBUG"
```

## Valid values

| Setting | Type | Rule |
| --- | --- | --- |
| `tui.interval` | number | Must be positive |
| `tui.stats_limit` | integer | Must be positive |
| `tui.chart_limit` | integer | Must be positive |
| `database.path` | string | `~` is expanded |
| `cli.default_history_limit` | integer | Must be positive |
| `cli.default_export_limit` | integer | Must be positive |
| `logging.level` | string | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

Very short intervals below `0.1` seconds are accepted but trigger a performance warning.
