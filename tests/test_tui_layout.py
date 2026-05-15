"""Tests for adaptive TUI layout selection."""

from datetime import UTC
from datetime import datetime

import pytest
from textual.geometry import Size

from powermonitor.config import PowerMonitorConfig
from powermonitor.models import PowerReading
from powermonitor.tui.app import PowerMonitorApp
from powermonitor.tui.layout import SIDE_BY_SIDE_MIN_TERMINAL_HEIGHT
from powermonitor.tui.layout import SIDE_BY_SIDE_MIN_TERMINAL_WIDTH
from powermonitor.tui.layout import STACKED_MIN_TERMINAL_HEIGHT
from powermonitor.tui.layout import STACKED_MIN_TERMINAL_WIDTH
from powermonitor.tui.layout import TUILayoutMode
from powermonitor.tui.layout import select_tui_layout
from powermonitor.tui.widgets import ChartWidget
from powermonitor.tui.widgets import LiveDataPanel


def _sample_reading(watts: float = 45.2) -> PowerReading:
    return PowerReading(
        timestamp=datetime.now(UTC),
        watts_actual=watts,
        watts_negotiated=67,
        voltage=20.0,
        amperage=2.26,
        current_capacity=3500,
        max_capacity=4709,
        battery_percent=74,
        is_charging=True,
        external_connected=True,
        charger_name="USB-C Power Adapter",
        charger_manufacturer="Apple Inc.",
    )


class FakeCollector:
    """Deterministic collector for TUI layout tests."""

    def __init__(self) -> None:
        self.reading = _sample_reading()

    def collect(self) -> PowerReading:
        return self.reading


class FakeDatabase:
    """In-memory database facade for TUI layout tests."""

    def __init__(self) -> None:
        self.readings: list[PowerReading] = []
        self.closed = False

    def insert_reading(self, reading: PowerReading) -> int:
        self.readings.append(reading)
        return len(self.readings)

    def query_history(self, limit: int | None = 20) -> list[PowerReading]:
        if limit is None:
            return list(reversed(self.readings))
        return list(reversed(self.readings[-limit:]))

    def get_statistics(self, limit: int | None = 100) -> dict:
        readings = self.readings if limit is None else self.readings[-limit:]
        if not readings:
            return {
                "count": 0,
                "avg_watts": 0.0,
                "min_watts": 0.0,
                "max_watts": 0.0,
                "avg_battery": 0.0,
                "earliest": None,
                "latest": None,
            }

        timestamps = [reading.timestamp for reading in readings]
        return {
            "count": len(readings),
            "avg_watts": sum(reading.watts_actual for reading in readings) / len(readings),
            "min_watts": min(reading.watts_actual for reading in readings),
            "max_watts": max(reading.watts_actual for reading in readings),
            "avg_battery": sum(reading.battery_percent for reading in readings) / len(readings),
            "earliest": min(timestamps).isoformat(),
            "latest": max(timestamps).isoformat(),
        }

    def clear_history(self) -> int:
        row_count = len(self.readings)
        self.readings.clear()
        return row_count

    def close(self) -> None:
        self.closed = True


def _test_app() -> PowerMonitorApp:
    return PowerMonitorApp(
        config=PowerMonitorConfig(collection_interval=999.0),
        collector=FakeCollector(),
        database=FakeDatabase(),
    )


def test_select_tui_layout_prefers_stacked_when_full_vertical_layout_fits() -> None:
    assert select_tui_layout(Size(STACKED_MIN_TERMINAL_WIDTH, STACKED_MIN_TERMINAL_HEIGHT)) == TUILayoutMode.STACKED
    assert select_tui_layout(Size(80, 40)) == TUILayoutMode.STACKED
    assert select_tui_layout(Size(60, 40)) == TUILayoutMode.STACKED


def test_select_tui_layout_uses_side_by_side_for_short_wide_terminals() -> None:
    assert (
        select_tui_layout(Size(SIDE_BY_SIDE_MIN_TERMINAL_WIDTH, SIDE_BY_SIDE_MIN_TERMINAL_HEIGHT))
        == TUILayoutMode.SIDE_BY_SIDE
    )
    assert select_tui_layout(Size(80, 24)) == TUILayoutMode.SIDE_BY_SIDE
    assert select_tui_layout(Size(120, 24)) == TUILayoutMode.SIDE_BY_SIDE


def test_select_tui_layout_avoids_side_by_side_when_terminal_is_too_narrow() -> None:
    mode = select_tui_layout(Size(SIDE_BY_SIDE_MIN_TERMINAL_WIDTH - 1, SIDE_BY_SIDE_MIN_TERMINAL_HEIGHT))

    assert mode == TUILayoutMode.COMPACT_STACKED


async def test_app_uses_stacked_layout_for_tall_terminal() -> None:
    app = _test_app()

    async with app.run_test(size=(80, 40)):
        layout_root = app.query_one("#layout-root")
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")

        assert TUILayoutMode.STACKED.value in layout_root.classes
        assert live_panel.region.y < stats_panel.region.y < chart.region.y
        assert live_panel.region.width == stats_panel.region.width
        assert chart.region.height >= 13


async def test_app_uses_side_by_side_layout_for_short_wide_terminal() -> None:
    app = _test_app()

    async with app.run_test(size=(120, 24)):
        layout_root = app.query_one("#layout-root")
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")

        assert TUILayoutMode.SIDE_BY_SIDE.value in layout_root.classes
        assert live_panel.region.y == stats_panel.region.y
        assert live_panel.region.x < stats_panel.region.x
        assert chart.region.y > live_panel.region.y
        assert chart.region.height >= 9


async def test_app_uses_compact_stacked_layout_for_short_narrow_terminal() -> None:
    app = _test_app()

    async with app.run_test(size=(60, 24)):
        layout_root = app.query_one("#layout-root")
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")

        assert TUILayoutMode.COMPACT_STACKED.value in layout_root.classes
        assert TUILayoutMode.SIDE_BY_SIDE.value not in layout_root.classes
        assert live_panel.region.y < stats_panel.region.y


@pytest.mark.parametrize(
    ("terminal_size", "expected_mode"),
    [
        ((80, 24), TUILayoutMode.SIDE_BY_SIDE),
        ((80, 40), TUILayoutMode.STACKED),
        ((120, 24), TUILayoutMode.SIDE_BY_SIDE),
        ((120, 40), TUILayoutMode.STACKED),
        ((60, 40), TUILayoutMode.STACKED),
    ],
)
async def test_app_layout_geometry_for_representative_terminal_sizes(
    terminal_size: tuple[int, int], expected_mode: TUILayoutMode
) -> None:
    app = _test_app()

    async with app.run_test(size=terminal_size):
        layout_root = app.query_one("#layout-root")
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")

        assert expected_mode.value in layout_root.classes
        assert chart.region.width > 0
        assert chart.region.height > 0

        if expected_mode == TUILayoutMode.SIDE_BY_SIDE:
            assert live_panel.region.y == stats_panel.region.y
            assert live_panel.region.x < stats_panel.region.x
            assert chart.region.height >= 9
        else:
            assert live_panel.region.y < stats_panel.region.y < chart.region.y
            assert chart.region.height >= 13


async def test_app_resize_changes_layout_without_replacing_widgets() -> None:
    app = _test_app()

    async with app.run_test(size=(120, 24)) as pilot:
        live_panel = app.query_one("#live-data", LiveDataPanel)
        chart = app.query_one("#chart", ChartWidget)
        initial_reading = live_panel.current_reading

        assert TUILayoutMode.SIDE_BY_SIDE.value in app.query_one("#layout-root").classes

        await pilot.resize_terminal(120, 40)
        await pilot.pause()

        assert TUILayoutMode.STACKED.value in app.query_one("#layout-root").classes
        assert app.query_one("#live-data", LiveDataPanel) is live_panel
        assert app.query_one("#chart", ChartWidget) is chart
        assert live_panel.current_reading is initial_reading

        next_reading = _sample_reading(watts=52.0)
        app.database.insert_reading(next_reading)
        app._update_all_widgets(next_reading)

        assert live_panel.current_reading == next_reading
        assert chart.readings[0] == next_reading
