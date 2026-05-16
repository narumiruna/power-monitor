---
title: FAQ
summary: Frequently asked questions about powermonitor, macOS battery monitoring, MacBook charging wattage, data storage, exports, and compatibility.
description: FAQ for powermonitor, a macOS battery monitor and MacBook charging wattage CLI, covering compatibility, data storage, exports, charger metadata, and battery health.
---

# FAQ

## What is powermonitor?

powermonitor is a Python CLI and Textual TUI for macOS battery monitoring and MacBook power usage tracking. It shows real-time wattage, voltage, amperage, battery percentage, charging state, charger metadata, history, charts, and battery health trends.

## Does powermonitor work on Apple Silicon and Intel Macs?

It is designed for macOS and uses IOKit/SMC data when available, with an `ioreg` fallback for broad compatibility. Exact sensors and charger fields can vary by Mac model, charger, cable, dock, and macOS version.

## Does powermonitor work on Windows or Linux?

No. powermonitor is macOS-only because it depends on macOS power APIs and `ioreg` output.

## Where is my MacBook power history stored?

By default, readings are stored locally in SQLite at:

```text
~/.powermonitor/powermonitor.db
```

You can change the path in `~/.powermonitor/config.toml`.

## Can I export MacBook battery and charging data?

Yes. Use CSV for spreadsheets or JSON for scripts and notebooks:

```bash
powermonitor export data.csv
powermonitor export data.json
```

## Can powermonitor show USB-C charger wattage?

powermonitor shows negotiated charger wattage, charger name, and manufacturer when macOS exposes that data. Some adapters, docks, cables, and Mac models expose less metadata than others.

## Is powermonitor an alternative to pmset, ioreg, or Activity Monitor?

It complements those tools. `pmset`, `ioreg`, Activity Monitor, and System Information expose useful power information, but powermonitor combines live wattage, battery status, charger details, local history, charts, and export commands in one terminal workflow.

## Does powermonitor require root privileges?

No. Normal usage does not require `sudo`.

## Does powermonitor send telemetry?

No. The app is local-first. Data leaves your machine only when you explicitly export it or share the database/export file yourself.

## How do I reduce database size?

Use cleanup commands:

```bash
powermonitor cleanup --days 30
powermonitor cleanup --all
```

## How do I change the refresh interval?

Use a one-time CLI override:

```bash
powermonitor --interval 2.0
```

Or set `[tui].interval` in `~/.powermonitor/config.toml`.

## Why do some readings or charger fields look unavailable?

macOS does not expose the same sensor set on every Mac, charger, cable, or dock. powermonitor records the values macOS provides and leaves unavailable fields empty or null in exports.
