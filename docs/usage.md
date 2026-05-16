---
title: TUI usage
summary: Use the powermonitor Textual TUI to watch live MacBook wattage, battery percentage, voltage, current, charger details, and charts.
description: User guide for the powermonitor real-time Textual TUI, including launch options, adaptive layout, keyboard controls, and Mac power metrics.
---

# TUI Usage

Running `powermonitor` without a subcommand opens the real-time Textual dashboard.

```bash
powermonitor
```

The TUI refreshes power data every second by default, saves readings to SQLite, and shows live metrics, rolling statistics, and a compact chart.

## Launch options

```bash
# Default real-time dashboard
powermonitor

# Collect every 2 seconds
powermonitor --interval 2.0

# Use larger history windows for statistics and charting
powermonitor --stats-limit 200 --chart-limit 120

# Enable debug logging
powermonitor --debug
```

| Option | Purpose | Default |
| --- | --- | --- |
| `--interval`, `-i` | Data collection interval in seconds | `1.0` |
| `--stats-limit` | Number of readings used for rolling statistics | `100` |
| `--chart-limit` | Number of readings shown in the chart | `60` |
| `--debug` | Enable debug logging | `false` |

CLI options override values from `~/.powermonitor/config.toml`. See [Configuration](configuration.md).

## Keyboard controls

| Key | Action |
| --- | --- |
| `q` | Quit |
| `Esc` | Quit |
| `r` | Force refresh |
| `c` | Clear history with confirmation |

## Dashboard panels

### Live data

The live panel shows current battery and charger information:

- Charging state: charging, AC power, or battery
- Actual power draw in watts
- Negotiated charger wattage when available
- Battery percentage
- Voltage and amperage
- Current and maximum battery capacity
- Charger name and manufacturer when macOS exposes them

### Statistics

The statistics panel summarizes recent readings:

- Time range
- Average, minimum, and maximum power
- Average battery percentage
- Sample count

The window size is controlled by `--stats-limit` or `[tui].stats_limit`.

### Power chart

The chart panel visualizes recent actual wattage and negotiated maximum power. The window size is controlled by `--chart-limit` or `[tui].chart_limit`.

## Adaptive layout

powermonitor adapts to terminal size:

- Tall terminals stack live data, statistics, and chart panels vertically.
- Short wide terminals place live data and statistics side by side above the chart.
- Narrow terminals avoid squeezing summary panels into unreadable columns.

The same widgets stay mounted while the layout changes, so resizing the terminal does not reset the dashboard data.

## Example dashboard

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

## Interpreting signs

Power readings may be positive or negative depending on charging state and sensor behavior. Use the status, external power flag, and battery percentage trend together when interpreting charging or draining behavior.
