---
title: Architecture
summary: Architecture of powermonitor collectors, Textual TUI, SQLite database, configuration, and CLI commands.
description: Technical architecture for powermonitor, a macOS battery monitor using IOKit/SMC, ioreg fallback collection, Textual UI, Typer CLI, and SQLite history.
---

# Architecture

powermonitor is a Python 3.13 package with a `src/` layout. The command-line interface, Textual TUI, power collectors, configuration loader, and SQLite persistence are kept in separate modules.

## High-level flow

```text
macOS power APIs
  ├─ IOKit/SMC collector (preferred)
  └─ ioreg collector (fallback)
          ↓
PowerReading dataclass
          ↓
SQLite database + live TUI widgets
          ↓
CLI history, stats, health, cleanup, and export commands
```

## Package layout

```text
src/powermonitor/
├── cli.py                 # Typer entry point and subcommands
├── config.py              # Validated PowerMonitorConfig dataclass
├── config_loader.py       # TOML loading and validation
├── database.py            # SQLite persistence through Peewee
├── logger.py              # Loguru setup
├── models.py              # PowerReading model
├── collector/
│   ├── base.py            # Collector protocol
│   ├── factory.py         # Automatic collector selection
│   ├── ioreg.py           # ioreg fallback collector
│   └── iokit/             # IOKit/SMC ctypes integration
└── tui/
    ├── app.py             # Textual application
    ├── layout.py          # Adaptive layout decisions
    └── widgets.py         # Live data, stats, and chart widgets
```

## Data collection

powermonitor uses automatic fallback:

1. **IOKitCollector** is preferred. It reads power data through macOS IOKit/SMC integration via `ctypes` and avoids subprocess overhead.
2. **IORegCollector** falls back to `ioreg -rw0 -c AppleSmartBattery -a` and parses plist output with the Python standard library.

This keeps the tool useful across Mac models where some sensors or charger fields may not be exposed consistently.

## TUI architecture

The Textual app has three primary widgets:

- `LiveDataPanel`: current watts, battery percentage, voltage, amperage, charger state, and charger metadata.
- `StatsPanel`: rolling statistics from recent readings.
- `ChartWidget`: recent power trend visualization.

`src/powermonitor/tui/layout.py` selects the most readable layout for the current terminal size. The app applies layout changes with stable widget IDs so resize events do not replace widgets or reset state.

## Persistence

Readings are saved to SQLite through `Database`, with context managers handling connection lifecycle. The default database path is:

```text
~/.powermonitor/powermonitor.db
```

The database stores readings used by history, stats, export, cleanup, and health commands.

## Configuration

`PowerMonitorConfig` owns validated runtime values. `config_loader.py` loads `~/.powermonitor/config.toml`, applies field-level fallback to defaults, and provides strict validation for `powermonitor config validate`.

Configuration priority is:

1. CLI arguments
2. Config file
3. Built-in defaults

## CLI design

The Typer app launches the TUI when invoked without a subcommand. Subcommands reuse the same config loader and database path so CLI output and TUI history stay consistent.
