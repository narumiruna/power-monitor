"""Adaptive layout rules for the powermonitor TUI."""

from enum import StrEnum

from textual.geometry import Size


class TUILayoutMode(StrEnum):
    """Layout modes selected from terminal geometry."""

    STACKED = "stacked"
    SIDE_BY_SIDE = "side-by-side"
    COMPACT_STACKED = "compact-stacked"


HEADER_FOOTER_HEIGHT = 2
SUMMARY_HORIZONTAL_MARGIN = 2
SUMMARY_TOP_MARGIN = 1
CHART_VERTICAL_MARGIN = 2
PANEL_HORIZONTAL_CHROME = 4
SIDE_BY_SIDE_PANEL_GAP = 1

STACKED_SUMMARY_HEIGHT = 22
SIDE_BY_SIDE_SUMMARY_HEIGHT = 10
COMPACT_STACKED_SUMMARY_HEIGHT = 14

STACKED_MIN_PANEL_CONTENT_WIDTH = 54
SIDE_BY_SIDE_MIN_PANEL_CONTENT_WIDTH = 30
STACKED_MIN_CHART_HEIGHT = 13
SIDE_BY_SIDE_MIN_CHART_HEIGHT = 9

STACKED_MIN_TERMINAL_WIDTH = SUMMARY_HORIZONTAL_MARGIN + PANEL_HORIZONTAL_CHROME + STACKED_MIN_PANEL_CONTENT_WIDTH
SIDE_BY_SIDE_MIN_TERMINAL_WIDTH = (
    SUMMARY_HORIZONTAL_MARGIN
    + SIDE_BY_SIDE_PANEL_GAP
    + (2 * (PANEL_HORIZONTAL_CHROME + SIDE_BY_SIDE_MIN_PANEL_CONTENT_WIDTH))
)
STACKED_MIN_TERMINAL_HEIGHT = (
    HEADER_FOOTER_HEIGHT
    + SUMMARY_TOP_MARGIN
    + STACKED_SUMMARY_HEIGHT
    + CHART_VERTICAL_MARGIN
    + STACKED_MIN_CHART_HEIGHT
)
SIDE_BY_SIDE_MIN_TERMINAL_HEIGHT = (
    HEADER_FOOTER_HEIGHT
    + SUMMARY_TOP_MARGIN
    + SIDE_BY_SIDE_SUMMARY_HEIGHT
    + CHART_VERTICAL_MARGIN
    + SIDE_BY_SIDE_MIN_CHART_HEIGHT
)


def stacked_layout_fits(size: Size) -> bool:
    """Return whether a terminal can show the full stacked layout."""
    return size.width >= STACKED_MIN_TERMINAL_WIDTH and size.height >= STACKED_MIN_TERMINAL_HEIGHT


def side_by_side_layout_fits(size: Size) -> bool:
    """Return whether a terminal can show readable side-by-side summary panels."""
    return size.width >= SIDE_BY_SIDE_MIN_TERMINAL_WIDTH and size.height >= SIDE_BY_SIDE_MIN_TERMINAL_HEIGHT


def select_tui_layout(size: Size) -> TUILayoutMode:
    """Select the most readable layout for a terminal size."""
    if stacked_layout_fits(size):
        return TUILayoutMode.STACKED
    if side_by_side_layout_fits(size):
        return TUILayoutMode.SIDE_BY_SIDE
    return TUILayoutMode.COMPACT_STACKED
