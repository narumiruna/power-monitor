---
title: Data and privacy
summary: Understand where powermonitor stores MacBook power history, what fields are saved, and how exports and cleanup work.
description: Data and privacy guide for powermonitor, covering the local SQLite database, saved power reading fields, CSV/JSON export, cleanup, and privacy model.
---

# Data and Privacy

powermonitor is local-first. It does not require a cloud account, daemon, telemetry service, or network connection for normal use.

## Local storage

By default, readings are stored in SQLite at:

```text
~/.powermonitor/powermonitor.db
```

You can change the location with `[database].path` in `~/.powermonitor/config.toml`. See [Configuration](configuration.md).

## What is stored

Each power reading can include:

- Timestamp
- Actual watts
- Negotiated charger watts
- Voltage
- Amperage
- Current battery capacity
- Maximum battery capacity
- Battery percentage
- Charging state
- External power state
- Charger name
- Charger manufacturer

Sensor availability depends on Mac model, charger, and macOS version. Missing charger metadata is stored as empty or null values in exports.

## Exports

Data leaves your machine only when you explicitly export it:

```bash
powermonitor export data.csv
powermonitor export data.json
```

CSV works well for spreadsheets and benchmark reports. JSON works well for scripts, notebooks, and downstream automation.

## Cleanup

Delete old data by age:

```bash
powermonitor cleanup --days 30
```

Delete all readings after confirmation:

```bash
powermonitor cleanup --all
```

Cleanup is manual and explicit. powermonitor does not silently remove history.

## Backups

To back up your history, copy the SQLite database while the TUI is not running, or export to CSV/JSON:

```bash
cp ~/.powermonitor/powermonitor.db ~/Documents/powermonitor-backup.db
powermonitor export ~/Documents/powermonitor-history.csv
```

## Privacy checklist

- No cloud sync is required.
- No account is required.
- No root privileges are required.
- Exports are user-initiated.
- Database path is configurable.
