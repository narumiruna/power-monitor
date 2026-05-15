"""Tests for TUI components."""

import sys
from datetime import UTC
from datetime import datetime

import pytest
from textual import events

from powermonitor import config_loader
from powermonitor.config import PowerMonitorConfig
from powermonitor.config import TUILayoutConfig
from powermonitor.models import PowerReading
from powermonitor.tui.app import PowerMonitorApp
from powermonitor.tui.layout import LayoutResizeHandle
from powermonitor.tui.widgets import LiveDataPanel
from powermonitor.tui.widgets import StatsPanel


@pytest.fixture
def sample_reading():
    """Sample power reading for testing."""
    return PowerReading(
        timestamp=datetime.now(UTC),
        watts_actual=45.2,
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


def test_live_data_panel_update(sample_reading):
    """Test LiveDataPanel updates with new reading."""
    panel = LiveDataPanel()

    # Initially should show waiting message
    initial = panel._render_reading()
    assert "Waiting for data" in initial

    # After update, should show reading data
    panel.update_reading(sample_reading)
    rendered = panel._render_reading()

    assert "45.2W" in rendered
    assert "74%" in rendered
    assert "Charging" in rendered


def test_stats_panel_empty():
    """Test StatsPanel with empty statistics."""
    panel = StatsPanel()

    empty_stats = {
        "count": 0,
        "avg_watts": 0.0,
        "min_watts": 0.0,
        "max_watts": 0.0,
        "avg_battery": 0.0,
        "earliest": None,
        "latest": None,
    }

    panel.update_stats(empty_stats)
    rendered = panel._render_stats()

    assert "No historical data" in rendered


def test_stats_panel_with_data():
    """Test StatsPanel with statistics data."""
    panel = StatsPanel()

    stats = {
        "count": 100,
        "avg_watts": 42.5,
        "min_watts": 12.3,
        "max_watts": 67.8,
        "avg_battery": 75.5,
        "earliest": "2025-01-05T10:00:00",
        "latest": "2025-01-05T10:10:00",
    }

    panel.update_stats(stats)
    rendered = panel._render_stats()

    assert "100 readings" in rendered
    assert "42.5W" in rendered
    assert "75.5%" in rendered


def test_layout_resize_handle_emits_mouse_drag_delta(monkeypatch):
    """Test LayoutResizeHandle emits drag deltas from mouse movement."""
    handle = LayoutResizeHandle(target="live_stats", axis="x")
    captured: list[bool] = []
    released: list[bool] = []
    messages: list[LayoutResizeHandle.Resized] = []
    monkeypatch.setattr(handle, "capture_mouse", lambda: captured.append(True))
    monkeypatch.setattr(handle, "release_mouse", lambda: released.append(True))
    monkeypatch.setattr(handle, "post_message", messages.append)

    handle.on_mouse_down(events.MouseDown(handle, 0, 0, 0, 0, 1, False, False, False, screen_x=10, screen_y=5))
    handle.on_mouse_move(events.MouseMove(handle, 0, 0, 3, 0, 1, False, False, False, screen_x=13, screen_y=5))
    handle.on_mouse_up(events.MouseUp(handle, 0, 0, 0, 0, 1, False, False, False, screen_x=13, screen_y=5))

    assert captured == [True]
    assert released == [True]
    assert len(messages) == 1
    assert messages[0].target == "live_stats"
    assert messages[0].axis == "x"
    assert messages[0].delta == 3


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_launches():
    """Test that PowerMonitorApp can launch without errors."""
    config = PowerMonitorConfig(collection_interval=1.0)
    app = PowerMonitorApp(config=config)

    async with app.run_test():
        # App should have header, footer, summary row, and 3 panels
        assert app.query_one("#summary-row") is not None
        assert app.query_one("#live-data") is not None
        assert app.query_one("#stats") is not None
        assert app.query_one("#chart") is not None


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_side_by_side_layout_styles():
    """Test side-by-side layout assigns configured row sizing."""
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(
            summary_mode="side_by_side",
            live_weight=2,
            stats_weight=3,
            summary_height=11,
            chart_height=16,
            panel_gap=2,
        ),
    )
    app = PowerMonitorApp(config=config)

    async with app.run_test():
        summary_row = app.query_one("#summary-row")
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")

        assert str(summary_row.styles.height) == "11"
        assert str(live_panel.styles.width) == "2fr"
        assert str(stats_panel.styles.width) == "3fr"
        assert str(chart.styles.height) == "16"
        assert summary_row.styles.margin.top == 2
        assert live_panel.styles.margin.right == 2


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_side_by_side_mouse_resize_updates_weights():
    """Test side-by-side resize messages update live and stats widths."""
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(summary_mode="side_by_side", live_weight=2, stats_weight=3),
    )
    app = PowerMonitorApp(config=config)

    async with app.run_test() as pilot:
        handle = app.query_one("#live-stats-resize", LayoutResizeHandle)
        handle.post_message(LayoutResizeHandle.Resized(handle, "live_stats", "x", 2))
        await pilot.pause()

        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        assert str(live_panel.styles.width) == "4fr"
        assert str(stats_panel.styles.width) == "1fr"


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_side_by_side_mouse_resize_updates_summary_and_chart_heights():
    """Test side-by-side vertical resize updates summary and chart heights."""
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(summary_mode="side_by_side", summary_height=10, chart_height=20),
    )
    app = PowerMonitorApp(config=config)

    async with app.run_test() as pilot:
        handle = app.query_one("#summary-chart-resize", LayoutResizeHandle)
        handle.post_message(LayoutResizeHandle.Resized(handle, "summary_chart", "y", 2))
        await pilot.pause()

        summary_row = app.query_one("#summary-row")
        chart = app.query_one("#chart")
        assert str(summary_row.styles.height) == "12"
        assert str(chart.styles.height) == "18"


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_stacked_layout_styles():
    """Test stacked layout omits summary row and assigns configured heights."""
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(
            summary_mode="stacked",
            live_height=7,
            stats_height=9,
            chart_height=15,
            panel_gap=2,
        ),
    )
    app = PowerMonitorApp(config=config)

    async with app.run_test():
        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")

        assert len(app.query("#summary-row")) == 0
        assert str(live_panel.styles.height) == "7"
        assert str(stats_panel.styles.height) == "9"
        assert str(chart.styles.height) == "15"
        assert live_panel.styles.margin.top == 2


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_stacked_mouse_resize_updates_heights_and_clamps():
    """Test stacked resize messages update panel heights and keep positive bounds."""
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(
            summary_mode="stacked",
            live_height=7,
            stats_height=9,
            chart_height=15,
        ),
    )
    app = PowerMonitorApp(config=config)

    async with app.run_test() as pilot:
        live_stats_handle = app.query_one("#stacked-live-stats-resize", LayoutResizeHandle)
        live_stats_handle.post_message(LayoutResizeHandle.Resized(live_stats_handle, "stacked_live_stats", "y", 2))
        await pilot.pause()

        stats_chart_handle = app.query_one("#stacked-stats-chart-resize", LayoutResizeHandle)
        stats_chart_handle.post_message(LayoutResizeHandle.Resized(stats_chart_handle, "stacked_stats_chart", "y", -10))
        await pilot.pause()

        live_panel = app.query_one("#live-data")
        stats_panel = app.query_one("#stats")
        chart = app.query_one("#chart")
        assert str(live_panel.styles.height) == "9"
        assert str(stats_panel.styles.height) == "1"
        assert str(chart.styles.height) == "25"


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_layout_mode_button_switches_between_modes():
    """Test layout mode control recomposes between side-by-side and stacked modes."""
    config = PowerMonitorConfig(collection_interval=1.0)
    app = PowerMonitorApp(config=config)

    async with app.run_test() as pilot:
        assert len(app.query("#summary-row")) == 1

        await pilot.click("#layout-mode-toggle")
        await pilot.pause()
        assert len(app.query("#summary-row")) == 0
        assert app.query_one("#stacked-live-stats-resize") is not None

        await pilot.click("#layout-mode-toggle")
        await pilot.pause()
        assert len(app.query("#summary-row")) == 1
        assert app.query_one("#live-stats-resize") is not None


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_save_layout_action_writes_runtime_layout(monkeypatch, tmp_path):
    """Test save layout action writes current runtime layout to the config file."""
    config_path = tmp_path / ".powermonitor" / "config.toml"
    monkeypatch.setattr(config_loader, "get_config_path", lambda: config_path)
    config = PowerMonitorConfig(
        collection_interval=1.0,
        layout=TUILayoutConfig(summary_mode="side_by_side", live_weight=2, stats_weight=3),
    )
    app = PowerMonitorApp(config=config)
    notifications: list[str] = []
    monkeypatch.setattr(app, "notify", lambda message, **kwargs: notifications.append(message))

    async with app.run_test() as pilot:
        handle = app.query_one("#live-stats-resize", LayoutResizeHandle)
        handle.post_message(LayoutResizeHandle.Resized(handle, "live_stats", "x", 2))
        await pilot.pause()

        app.action_save_layout()
        await pilot.pause()

    saved_config = config_path.read_text(encoding="utf-8")
    assert 'summary_mode = "side_by_side"' in saved_config
    assert "live_weight = 4" in saved_config
    assert "stats_weight = 1" in saved_config
    assert config_loader.validate_config_file(config_path).is_valid
    assert any("Saved layout to" in notification for notification in notifications)


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
def test_app_save_layout_action_reports_failure(monkeypatch):
    """Test save layout action reports config write failures."""
    app = PowerMonitorApp(config=PowerMonitorConfig(collection_interval=1.0))
    notifications: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        config_loader,
        "save_layout_config",
        lambda layout: (_ for _ in ()).throw(ValueError("boom")),
    )
    monkeypatch.setattr(app, "notify", lambda message, **kwargs: notifications.append((message, kwargs)))

    app.action_save_layout()

    assert notifications == [("Failed to save layout: boom", {"severity": "error", "timeout": 5})]


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="PowerMonitorApp requires macOS collector",
)
async def test_app_refresh_action():
    """Test that refresh action works."""
    config = PowerMonitorConfig(collection_interval=1.0)
    app = PowerMonitorApp(config=config)

    async with app.run_test() as pilot:
        # Trigger refresh action
        await pilot.press("r")

        # Should show notification
        # (actual verification would require mocking collector)
