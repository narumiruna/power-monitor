# Adaptive TUI Layout Plan

## Goal

Make the powermonitor TUI choose the most readable layout from the available terminal size:
use stacked panels when there is enough vertical space for the live panel, stats panel, and chart to display normally,
and fall back to side-by-side summary panels when vertical space is tight. Apply the analogous horizontal rule so narrow
terminals avoid side-by-side summary panels when each panel would become too cramped.

Success means the TUI automatically selects a layout from the current terminal geometry, responds to resize events, and
keeps the chart readable in all supported viewport sizes.

## Context

The current `main` branch uses a fixed side-by-side summary row in `src/powermonitor/tui/app.py`:
`Vertical(Horizontal(LiveDataPanel, StatsPanel), ChartWidget)`. Commit `67aaa40` changed the previous fixed stacked
layout into this side-by-side shape. Current CSS fixes `#summary-row` at height `10` and `#chart` at height `20`, so a
short terminal can still place part of the chart below the visible area.

There are older unmerged branches with configurable and mouse-resizable layout work (`narumi/tui-summary-row-layout` and
`narumi/mouse-resizable-tui-layout`). Those branches are useful reference material, but this plan should keep the first
adaptive implementation smaller than reintroducing user-configurable or persisted layout state.

Local Textual evidence:

- The project has Textual `7.0.0` installed.
- `App.run_test(size=(width, height))` can exercise layout behavior in tests.
- `textual.events.Resize` exists and can be used to recompute layout after terminal size changes.
- Textual CSS `layout: horizontal` / `layout: vertical` on a stable `Container` provides the needed base layout
  primitives.

## Non-Goals

- Do not add persisted layout preferences in the first slice.
- Do not reintroduce mouse-resizable handles in the first slice.
- Do not change collector, database, or chart data semantics.
- Do not add a new dependency unless Textual's existing APIs cannot support deterministic size checks.

## Assumptions

- "Chart displays normally" means the chart widget receives at least a defined minimum content height and width after
  border, padding, header, footer, and margins are accounted for.
- The first implementation can use fixed minimum dimensions for each layout mode, then adjust if visual testing shows
  the chart or summary panels need different thresholds.
- Automatic layout selection is preferred over a config option unless later user feedback asks for manual override.

## Resolved Decisions

- Minimum layout thresholds are encoded in `src/powermonitor/tui/layout.py` and covered by pure helper tests.
- Resize uses stable container IDs plus CSS class updates in `PowerMonitorApp._apply_layout_mode()`, not `recompose()`, so
  mounted widgets and their data survive mode changes.
- Terminals below the full readable stacked and side-by-side thresholds use `compact-stacked` as a fallback. It avoids
  unreadably narrow side-by-side summary panels without making tiny terminal dimensions a full-readability guarantee.

## Architecture

Keep layout decision logic separate from data collection and widget rendering. A small TUI-local helper can convert a
terminal `Size` into a layout mode, for example:

- `stacked`: live panel, stats panel, and chart in one vertical column.
- `side_by_side`: live and stats panels in a horizontal summary row above the chart.
- `compact_stacked`: fallback for terminals that are too narrow or short for the full readable modes.

`PowerMonitorApp` should own applying the selected layout mode because it composes the TUI tree. `ChartWidget`,
`LiveDataPanel`, and `StatsPanel` should not need to know why the mode changed.

## Plan

- [x] Measure current layout behavior at representative terminal sizes (`80x24`, `80x40`, `120x24`, `120x40`,
  `60x40`) and record widget regions for `#live-data`, `#stats`, and `#chart`; verified by
  `tests/test_tui_layout.py::test_app_layout_geometry_for_representative_terminal_sizes`.
- [x] Define minimum readable dimensions for each panel and chart in a TUI-local helper, producing a deterministic mode
  decision from terminal width and height; verified by `src/powermonitor/tui/layout.py` and the
  `test_select_tui_layout_*` boundary tests.
- [x] Choose the resize application strategy for `PowerMonitorApp` after a small spike: stable container IDs and a single
  `_apply_layout_mode()` method using CSS classes; verified by `test_app_resize_changes_layout_without_replacing_widgets`.
- [x] Update `src/powermonitor/tui/app.py` so initial composition uses the helper-selected layout for the current screen
  size; verified by Textual `run_test(size=...)` tests for tall/wide stacked layout and short-but-wide side-by-side
  layout.
- [x] Add resize handling in `PowerMonitorApp` so changing terminal dimensions recomputes the layout mode only when the
  selected mode changes; verified by `test_app_resize_changes_layout_without_replacing_widgets`.
- [x] Preserve data refresh behavior while layouts switch by keeping widget IDs stable and ensuring `_update_all_widgets`
  can still query the same widgets; verified by existing TUI tests plus
  `test_app_resize_changes_layout_without_replacing_widgets`.
- [x] Add horizontal fallback coverage for narrow terminals so side-by-side mode is not used when live and stats panels
  would each fall below the minimum readable width; verified by
  `test_select_tui_layout_avoids_side_by_side_when_terminal_is_too_narrow` and
  `test_app_uses_compact_stacked_layout_for_short_narrow_terminal`.
- [x] Update README TUI documentation to describe the adaptive layout behavior without documenting internal thresholds
  as a user contract; verified by reviewing `README.md` TUI usage and architecture text.
- [x] Run the final quality gate for this slice; verified by `make all` with 156 passed and 2 skipped.

## Risks

- Recomposition on every resize event can cause flicker or drop widget state; mitigated by CSS class changes on a stable
  `#layout-root` and a resize test that asserts widget identity survives.
- Hard-coded thresholds can age poorly if panel content grows, especially the charger line in `LiveDataPanel`; accepted
  for this first slice because thresholds are centralized in `src/powermonitor/tui/layout.py`.
- `textual-plotext` may require more height than the container's nominal content height suggests; mitigated by Textual
  geometry tests that assert chart widget region height for representative stacked and side-by-side sizes.
- Very small terminals may not be able to show any layout "normally"; mitigated by an explicit `compact-stacked` fallback
  that avoids side-by-side squeezing without treating tiny viewports as fully readable.

## Rollback / Recovery

- Revert the adaptive helper and `PowerMonitorApp` layout changes to return to the current fixed side-by-side layout if
  resize behavior causes flicker or broken widget updates.
- Keep README changes in the same implementation commit as the adaptive behavior so rollback does not leave stale
  documentation.

## Completion Checklist

- [x] Stacked mode is selected when live, stats, and chart widgets all meet their minimum readable dimensions, verified
  by helper unit tests and Textual `run_test(size=...)` layout assertions.
- [x] Side-by-side mode is selected when vertical space is insufficient for stacked layout but horizontal width can
  support readable summary panels, verified by boundary-size tests.
- [x] Narrow terminal behavior avoids unreadable side-by-side summary panels, verified by a dedicated narrow-width test
  and `compact-stacked` fallback coverage.
- [x] Runtime terminal resize updates the layout mode without losing widget data, verified by
  `test_app_resize_changes_layout_without_replacing_widgets` and existing TUI update tests.
- [x] The README describes adaptive TUI behavior accurately, verified by reviewing the updated TUI section against the
  implemented mode rules.
- [x] The implementation passes repository quality checks, verified by `make lint`, `make type`, `make test`, and
  `make all`.
