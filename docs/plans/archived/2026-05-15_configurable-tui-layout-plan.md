# Configurable TUI Layout Plan

## Goal

Let users choose the TUI panel arrangement and panel sizes from `~/.powermonitor/config.toml`.
The first complete outcome is a tested config-driven layout system that can:

- Put live charging data and stats side by side in the same row.
- Move live charging data and stats back to separate stacked rows.
- Adjust the relative width or height of those panels and the chart height.

## Context

The TUI layout is currently hard-coded in `src/powermonitor/tui/app.py`. The config system already loads `[tui]`
settings from `src/powermonitor/config_loader.py` into `PowerMonitorConfig`, and recent CLI work added
`powermonitor config init`, `show`, and `validate`.

## Architecture

Add a small layout config object owned by `PowerMonitorConfig`, then have `PowerMonitorApp` compose and size widgets
from that object.

Proposed config shape:

```toml
[tui.layout]
summary_mode = "side_by_side" # side_by_side or stacked
live_weight = 1
stats_weight = 1
live_height = 8
stats_height = 10
summary_height = 10
chart_height = 20
panel_gap = 1
```

Behavior:

- `summary_mode = "side_by_side"` renders `LiveDataPanel` and `StatsPanel` inside a `Horizontal` row.
- `summary_mode = "stacked"` renders `LiveDataPanel`, then `StatsPanel`, then `ChartWidget`.
- `live_weight` and `stats_weight` apply only to `side_by_side` mode.
- `live_height` and `stats_height` apply only to `stacked` mode.
- `summary_height`, `chart_height`, and `panel_gap` apply to both modes where relevant.

## Non-Goals

- Do not add drag-and-drop panel rearrangement in the first slice.
- Do not add dynamic config reload while the TUI is running.
- Do not let users define arbitrary widget trees or plugin panels.
- Do not add dependencies; use existing dataclasses, Typer, Textual, and TOML loading.

## Assumptions

- The default layout should match the current side-by-side summary row.
- Users can restart the TUI after editing config for the layout to take effect.
- Bounded numeric settings are enough for the first slice; exact terminal fit still depends on terminal size.

## Unknowns

- Resolved: use positive integer size values and keep readability as a documented user responsibility for this slice.
  The implementation verifies that configured values are assigned correctly, but does not enforce opinionated minimums.
- Resolved: invalid layout values fail `powermonitor config validate`, while runtime loading falls back per invalid field
  to preserve the existing forgiving config-loader behavior.

## Plan

- [x] Define `TUILayoutConfig` in `src/powermonitor/config.py` with `summary_mode`, width weights, heights, and gap
  fields; verify valid defaults and invalid values in `tests/test_config.py`.
- [x] Extend `PowerMonitorConfig` to own `layout: TUILayoutConfig` without changing existing collection, history, or
  database settings; verify existing config tests still pass.
- [x] Extend `src/powermonitor/config_loader.py` to parse `[tui.layout]` with the same forgiving runtime behavior as
  other config fields; verify with `tests/test_config_loader.py` for valid layout config, invalid numeric values,
  invalid `summary_mode`, unknown nested keys, and fallback defaults.
- [x] Extend `validate_config_file()` to report strict errors for invalid layout values and unknown `[tui.layout]` keys;
  verify with CLI tests for `powermonitor config validate`.
- [x] Update `default_config_toml()` and `powermonitor config show` so layout defaults are visible to users; verify with
  CLI tests that `init` writes valid TOML and `show` includes layout mode and size values.
- [x] Update `PowerMonitorApp.compose()` to choose stacked or side-by-side composition from `config.layout`; verify with
  TUI tests that `summary_mode = "side_by_side"` creates `#summary-row` and `summary_mode = "stacked"` does not.
- [x] Apply layout sizing and gaps through Textual styles from `config.layout` instead of hard-coded CSS margins; verify
  with TUI tests that configured heights and weights are assigned to the expected widgets.
- [x] Update `README.md` with examples for side-by-side layout, stacked layout, and size tuning; verify examples match
  `powermonitor config init` output and accepted validation keys.
- [x] Run final quality gates with `make all` and `uv build --no-sources`.

## Risks

- Textual sizing semantics can be surprising if height, width, and margins are mixed between CSS and Python styles.
- Very small configured heights can make panels unreadable even if the values are syntactically valid.
- Nested `[tui.layout]` validation can diverge from runtime loading if structure checks are duplicated instead of shared.
- Making layout too generic too early can turn a simple preference into a fragile UI schema.

## Rollback / Recovery

- If configurable layout breaks TUI startup, revert the layout config fields and return `PowerMonitorApp.compose()` to
  the hard-coded current layout.
- If a release ships with broken layout config parsing, keep the config keys ignored at runtime and ship a patch that
  restores the fixed default layout while preserving existing non-layout config behavior.

## Completion Checklist

- [x] Users can choose side-by-side or stacked live/stats layout, verified by TUI tests and a bounded
  `PowerMonitorApp.run_test()` smoke run.
- [x] Users can tune live/stats/chart sizes, verified by config loader tests and TUI style assertions.
- [x] Invalid layout config is rejected by `powermonitor config validate`, verified by CLI tests.
- [x] Runtime config loading remains forgiving for invalid layout values, verified by config loader fallback tests.
- [x] README examples and generated default config use the same keys, verified by comparing docs against
  `uv run powermonitor config init` output.
- [x] Repository quality gates pass, verified with `make all` and `uv build --no-sources`.

## Completion Evidence

- `uv run pytest tests/test_config.py tests/test_config_loader.py tests/test_cli.py tests/test_tui.py`: passed.
- `make all`: passed.
- `uv build --no-sources`: passed.
- `uv run powermonitor config init` with a temporary HOME generated `[tui.layout]` defaults, and
  `uv run powermonitor config validate` accepted that generated file.
- `PowerMonitorApp.run_test()` with `summary_mode = "stacked"` launched successfully and applied configured live, stats,
  and chart heights.
