---
title: CLI command reference
summary: Command reference for powermonitor history, stats, health, export, cleanup, and config commands.
description: powermonitor CLI reference for exporting MacBook battery data, viewing history, checking battery health, cleaning SQLite history, and managing configuration.
---

# CLI Commands

`powermonitor` launches the TUI by default and also provides scriptable commands for history, export, database inspection, cleanup, battery health, and configuration.

## Command summary

| Command | What it does |
| --- | --- |
| `powermonitor` | Launches the real-time Textual dashboard |
| `powermonitor export OUTPUT` | Exports saved readings as CSV or JSON |
| `powermonitor stats` | Shows database count, date range, size, and path |
| `powermonitor history` | Prints recent power readings in a table |
| `powermonitor health` | Summarizes battery capacity changes over time |
| `powermonitor cleanup` | Deletes old readings or clears the local database |
| `powermonitor config` | Creates, shows, and validates `config.toml` |

Use `powermonitor COMMAND --help` for exact options.

## Export readings

Export power readings to CSV or JSON:

```bash
# Auto-detect CSV from extension
powermonitor export data.csv

# Auto-detect JSON from extension
powermonitor export data.json

# Export the last 1000 readings
powermonitor export data.csv --limit 1000

# Force a format when the extension is not enough
powermonitor export backup.txt --format csv
```

Exported fields include timestamp, actual watts, negotiated watts, voltage, amperage, battery percentage, capacity values, charging flags, and charger metadata.

## Show database statistics

```bash
powermonitor stats
```

Example output:

```text
Database Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total readings       12,450
Earliest reading     2025-12-01 10:30:00
Latest reading       2026-01-06 15:22:00
Database size        2.40 MB
Database path        /Users/you/.powermonitor/powermonitor.db
```

## View recent history

```bash
# Show the default number of readings
powermonitor history

# Show the last 50 readings
powermonitor history --limit 50
```

History output includes time, power, battery percentage, voltage, current, and status.

## Analyze battery health

```bash
# Analyze the last 30 days
powermonitor health

# Analyze the last 60 days
powermonitor health --days 60
```

The command compares daily average maximum capacity values and labels the trend as stable, normal wear, or significant degradation based on the observed percentage change.

## Clean up saved data

```bash
# Delete readings older than 30 days
powermonitor cleanup --days 30

# Delete all readings after confirmation
powermonitor cleanup --all
```

Cleanup only affects the local SQLite database configured for powermonitor.

## Manage configuration

```bash
powermonitor config init
powermonitor config show
powermonitor config validate
```

See [Configuration](configuration.md) for the TOML format and precedence rules.
