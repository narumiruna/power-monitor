# Mouse-Resizable TUI Layout Plan

## Goal

Let users adjust the powermonitor TUI layout with the mouse while the TUI is running.
The first complete outcome is a tested interaction model that can:

- Drag a divider between live charging data and stats to resize their space.
- Drag a divider between summary content and the chart to resize chart space.
- Switch between side-by-side and stacked summary layout from inside the TUI.
- Save the adjusted layout back to `~/.powermonitor/config.toml` only through an explicit user action.

## Context

The current TUI layout is composed in `src/powermonitor/tui/app.py` from `PowerMonitorConfig.layout`.
The persistent layout schema already exists as `TUILayoutConfig` in `src/powermonitor/config.py`, with
`summary_mode`, panel weights, panel heights, chart height, and panel gap. The local Textual version is 7.0.0 and
provides `MouseDown`, `MouseMove`, `MouseUp`, and `Widget.capture_mouse()` for drag interactions. Textual's test
pilot supports mouse down/up and can be supplemented with direct event posting or small widget-level tests for drag
movement.

## Architecture

- Keep `TUILayoutConfig` as the durable layout model.
- Add a mutable runtime layout copy inside `PowerMonitorApp` so mouse drags can update styles without mutating the
  loaded config object accidentally.
- Add dedicated resize handle widgets in `src/powermonitor/tui/layout.py`:
  - A vertical handle between live data and stats in `side_by_side` mode.
  - Horizontal handles between stacked panels and the chart where vertical height can change.
- Add a small in-TUI layout mode control that changes `summary_mode` and recomposes the layout.
- Add an explicit save action that writes the current runtime layout values to the config file through config-loader
  support, then validates that the saved file can be loaded.

## Non-Goals

- Do not add arbitrary drag-and-drop widget reordering in this slice.
- Do not autosave every mouse drag.
- Do not add a new layout dependency or a full TOML round-trip library unless preserving existing config content is
  impossible with the current config-loader approach.
- Do not redesign the TUI theme beyond adding clear resize handles and a layout mode control.

## Assumptions

- Mouse-based layout changes should affect the current TUI session immediately.
- Persisting changes should require an explicit user action to avoid surprising writes to `~/.powermonitor/config.toml`.
- Existing config-file layout keys remain the source of truth when the app starts.
- Keyboard/config-file editing remains the fallback for terminals where mouse reporting is unavailable.

## Unknowns

- Resolved: `Pilot` covers click and mounted wiring, while resize drag deltas are verified through
  `LayoutResizeHandle` mouse-event tests plus mounted resize message tests.
- Resolved: saving layout uses targeted `[tui.layout]` replacement or insertion so unrelated config sections remain
  intact.
- Resolved: the first slice provides both clickable TUI buttons and keyboard bindings for layout toggle and save.

## Plan

- [x] Spike Textual mouse test coverage with a minimal resize-handle prototype that captures mouse on `MouseDown`,
  updates a delta on `MouseMove`, and releases on `MouseUp`; verify with `uv run pytest tests/test_tui.py -k resize`.
- [x] Add `src/powermonitor/tui/layout.py` with `LayoutResizeHandle`, resize-axis metadata, and emitted resize messages
  to isolate mouse event handling from `PowerMonitorApp`; verify with focused tests for capture, delta emission, and
  release behavior.
- [x] Refactor `PowerMonitorApp` to keep a runtime `TUILayoutConfig` copy and a helper that applies layout styles to
  mounted widgets; verify existing layout tests still pass with `uv run pytest tests/test_tui.py`.
- [x] Add side-by-side mouse resizing so dragging the live/stats divider updates `live_weight` and `stats_weight` within
  positive integer bounds; verify with a TUI test that a drag changes the expected panel width styles.
- [x] Add vertical resizing so dragging summary/chart or stacked-panel dividers updates `summary_height`, `live_height`,
  `stats_height`, and `chart_height` within positive integer bounds; verify with TUI tests for both `side_by_side` and
  `stacked` modes.
- [x] Add a clickable in-TUI layout mode control that switches between `side_by_side` and `stacked`, recomposes the
  panel structure, and refreshes current readings/statistics after recompose; verify with a `run_test()` that the
  `#summary-row` appears and disappears after switching modes.
- [x] Add explicit save-layout support to the config loader or CLI support module so current runtime layout values are
  written to `~/.powermonitor/config.toml` without changing non-layout runtime behavior; verify with a temp HOME test
  that saved TOML validates and reloads into the same `TUILayoutConfig`.
- [x] Add a TUI action and visible feedback for saving layout changes; verify with a mocked config path test that the
  action writes layout values and shows success or failure notification without exiting the TUI.
- [x] Update `README.md` with mouse resize handles, layout mode switching, save behavior, and config-file fallback;
  verify examples match the accepted `[tui.layout]` keys and `powermonitor config validate`.
- [x] Run final quality gates with `make all` and `uv build --no-sources`.

## Risks

- Mitigated: Terminal mouse reporting varies, so config-file editing remains documented as a reliable fallback.
- Mitigated: Textual drag behavior is covered by resize-handle mouse-event tests plus mounted resize message tests.
- Mitigated: Saving config from inside the TUI replaces or inserts only the `[tui.layout]` table.
- Mitigated: Layout mode switching recomposes the TUI and refreshes mounted widgets from the cached latest reading.

## Rollback / Recovery

- If mouse drag behavior proves unreliable, keep the static config-driven layout and remove only the resize handle
  widgets and mouse event handlers.
- If config persistence is risky, ship runtime-only mouse resizing first and keep explicit save-layout support as a
  follow-up plan item.
- If layout mode switching causes TUI instability, keep resizing within the currently configured `summary_mode` and
  continue using config-file edits for mode changes.

## Completion Evidence

- `uv run pytest tests/test_tui.py -k resize`: passed.
- `uv run pytest tests/test_tui.py tests/test_config_loader.py`: passed.
- `make all`: passed, with 176 passed and 2 skipped.
- `uv build --no-sources`: passed.

## Completion Checklist

- [x] Users can resize live/stats space with the mouse in side-by-side mode, verified by TUI tests that inspect updated
  `live_weight` and `stats_weight` styles.
- [x] Users can resize summary, stacked panels, and chart height with the mouse, verified by TUI tests for both layout
  modes and positive-bound clamping.
- [x] Users can switch between side-by-side and stacked layout from inside the TUI, verified by a `run_test()` that
  checks `#summary-row` before and after the mode switch.
- [x] Users can explicitly save mouse-adjusted layout values to config, verified by a temp HOME test that validates and
  reloads the saved TOML.
- [x] Existing config-file layout behavior remains compatible, verified by existing `tests/test_config.py`,
  `tests/test_config_loader.py`, `tests/test_cli.py`, and `tests/test_tui.py`.
- [x] User documentation explains mouse resizing, save behavior, and config fallback, verified by README review against
  current TUI controls and `[tui.layout]` keys.
- [x] Repository quality gates pass, verified with `make all` and `uv build --no-sources`.
