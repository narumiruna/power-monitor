"""powermonitor Textual TUI Application - auto-updating power monitoring interface."""

import asyncio
import contextlib
from dataclasses import replace

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header

from .. import config_loader
from ..collector import default_collector
from ..config import PowerMonitorConfig
from ..database import Database
from ..models import PowerReading
from .layout import LayoutResizeHandle
from .widgets import ChartWidget
from .widgets import LiveDataPanel
from .widgets import StatsPanel

MIN_LAYOUT_SIZE = 1


class PowerMonitorApp(App):
    """powermonitor TUI application with auto-updating power data.

    Features:
    - Real-time power monitoring (updates every 1s by default)
    - Historical statistics and trends
    - Interactive chart showing power over time
    - Automatic data persistence to SQLite
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #live-data {
        border: solid green;
        padding: 1;
    }

    #stats {
        border: solid cyan;
        padding: 1;
    }

    #chart {
        border: solid blue;
        padding: 1;
    }

    #layout-controls {
        height: 3;
        margin: 1 1 0 1;
    }

    #layout-mode-toggle {
        width: 1fr;
        margin: 0 1 0 0;
    }

    #layout-save {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("escape", "quit", "Quit", show=False),
        Binding("c", "clear_history", "Clear History", key_display="C"),
        Binding("l", "toggle_layout", "Layout", key_display="L"),
        Binding("s", "save_layout", "Save Layout", key_display="S"),
    ]

    TITLE = "powermonitor - macOS Power Monitoring"

    def __init__(self, config: PowerMonitorConfig | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or PowerMonitorConfig()
        self.collector = default_collector()
        self.database = Database(self.config.database_path)
        self._collector_task: asyncio.Task | None = None
        self._runtime_layout = replace(self.config.layout)
        self._last_reading: PowerReading | None = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout.

        Top row:
        - LiveDataPanel: Real-time power data
        - StatsPanel: Historical statistics

        Bottom row:
        - ChartWidget: Power over time chart
        """
        layout = self._runtime_layout
        live_panel = LiveDataPanel(id="live-data")
        stats_panel = StatsPanel(id="stats")
        chart = ChartWidget(id="chart")
        controls = Horizontal(
            Button(self._layout_toggle_label(), id="layout-mode-toggle"),
            Button("Save layout", id="layout-save"),
            id="layout-controls",
        )
        chart.styles.height = layout.chart_height
        chart.styles.margin = (layout.panel_gap, layout.panel_gap, layout.panel_gap, layout.panel_gap)

        yield Header()
        yield controls
        if layout.summary_mode == "side_by_side":
            live_stats_handle = LayoutResizeHandle(
                target="live_stats",
                axis="x",
                id="live-stats-resize",
                classes="vertical",
            )
            live_stats_handle.styles.width = 1
            live_stats_handle.styles.height = "100%"
            summary_row = Horizontal(live_panel, live_stats_handle, stats_panel, id="summary-row")
            summary_row.styles.height = layout.summary_height
            summary_row.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
            live_panel.styles.width = f"{layout.live_weight}fr"
            live_panel.styles.height = "100%"
            live_panel.styles.margin = (0, layout.panel_gap, 0, 0)
            stats_panel.styles.width = f"{layout.stats_weight}fr"
            stats_panel.styles.height = "100%"
            summary_chart_handle = LayoutResizeHandle(
                target="summary_chart",
                axis="y",
                id="summary-chart-resize",
                classes="horizontal",
            )
            self._style_horizontal_handle(summary_chart_handle)
            yield Vertical(summary_row, summary_chart_handle, chart)
        else:
            live_stats_handle = LayoutResizeHandle(
                target="stacked_live_stats",
                axis="y",
                id="stacked-live-stats-resize",
                classes="horizontal",
            )
            stats_chart_handle = LayoutResizeHandle(
                target="stacked_stats_chart",
                axis="y",
                id="stacked-stats-chart-resize",
                classes="horizontal",
            )
            self._style_horizontal_handle(live_stats_handle)
            self._style_horizontal_handle(stats_chart_handle)
            live_panel.styles.height = layout.live_height
            live_panel.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
            stats_panel.styles.height = layout.stats_height
            stats_panel.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
            yield Vertical(live_panel, live_stats_handle, stats_panel, stats_chart_handle, chart)
        yield Footer()

    def _layout_toggle_label(self) -> str:
        """Return the mode-toggle button label for the current runtime layout."""
        return "Stacked layout" if self._runtime_layout.summary_mode == "side_by_side" else "Side-by-side layout"

    def _style_horizontal_handle(self, handle: LayoutResizeHandle) -> None:
        """Apply shared styles for horizontal resize handles."""
        handle.styles.height = 1
        handle.styles.width = "1fr"
        handle.styles.margin = (0, self._runtime_layout.panel_gap, 0, self._runtime_layout.panel_gap)

    def _replace_runtime_layout(self, **changes: object) -> None:
        """Update the runtime layout and apply it to mounted widgets."""
        self._runtime_layout = replace(self._runtime_layout, **changes)
        self._apply_runtime_layout_styles()

    def _apply_runtime_layout_styles(self) -> None:
        """Apply runtime layout values to currently mounted widgets."""
        layout = self._runtime_layout

        with contextlib.suppress(Exception):
            toggle = self.query_one("#layout-mode-toggle", Button)
            toggle.label = self._layout_toggle_label()

        with contextlib.suppress(Exception):
            chart = self.query_one("#chart", ChartWidget)
            chart.styles.height = layout.chart_height
            chart.styles.margin = (layout.panel_gap, layout.panel_gap, layout.panel_gap, layout.panel_gap)

        if layout.summary_mode == "side_by_side":
            with contextlib.suppress(Exception):
                summary_row = self.query_one("#summary-row")
                live_panel = self.query_one("#live-data")
                stats_panel = self.query_one("#stats")
                live_stats_handle = self.query_one("#live-stats-resize", LayoutResizeHandle)
                summary_chart_handle = self.query_one("#summary-chart-resize", LayoutResizeHandle)

                summary_row.styles.height = layout.summary_height
                summary_row.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
                live_panel.styles.width = f"{layout.live_weight}fr"
                live_panel.styles.height = "100%"
                live_panel.styles.margin = (0, layout.panel_gap, 0, 0)
                live_stats_handle.styles.width = 1
                live_stats_handle.styles.height = "100%"
                stats_panel.styles.width = f"{layout.stats_weight}fr"
                stats_panel.styles.height = "100%"
                self._style_horizontal_handle(summary_chart_handle)
        else:
            with contextlib.suppress(Exception):
                live_panel = self.query_one("#live-data")
                stats_panel = self.query_one("#stats")
                live_stats_handle = self.query_one("#stacked-live-stats-resize", LayoutResizeHandle)
                stats_chart_handle = self.query_one("#stacked-stats-chart-resize", LayoutResizeHandle)

                live_panel.styles.height = layout.live_height
                live_panel.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
                stats_panel.styles.height = layout.stats_height
                stats_panel.styles.margin = (layout.panel_gap, layout.panel_gap, 0, layout.panel_gap)
                self._style_horizontal_handle(live_stats_handle)
                self._style_horizontal_handle(stats_chart_handle)

    @staticmethod
    def _adjust_pair(first: int, second: int, delta: int) -> tuple[int, int]:
        """Adjust a pair of positive integer sizes by a drag delta."""
        return max(MIN_LAYOUT_SIZE, first + delta), max(MIN_LAYOUT_SIZE, second - delta)

    def on_layout_resize_handle_resized(self, message: LayoutResizeHandle.Resized) -> None:
        """Apply resize-handle drag deltas to the runtime layout."""
        layout = self._runtime_layout
        match message.target:
            case "live_stats":
                live_weight, stats_weight = self._adjust_pair(layout.live_weight, layout.stats_weight, message.delta)
                self._replace_runtime_layout(live_weight=live_weight, stats_weight=stats_weight)
            case "summary_chart":
                summary_height, chart_height = self._adjust_pair(
                    layout.summary_height,
                    layout.chart_height,
                    message.delta,
                )
                self._replace_runtime_layout(summary_height=summary_height, chart_height=chart_height)
            case "stacked_live_stats":
                live_height, stats_height = self._adjust_pair(layout.live_height, layout.stats_height, message.delta)
                self._replace_runtime_layout(live_height=live_height, stats_height=stats_height)
            case "stacked_stats_chart":
                stats_height, chart_height = self._adjust_pair(layout.stats_height, layout.chart_height, message.delta)
                self._replace_runtime_layout(stats_height=stats_height, chart_height=chart_height)
        message.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle clickable layout controls."""
        if event.button.id == "layout-mode-toggle":
            self.action_toggle_layout()
            event.stop()
        elif event.button.id == "layout-save":
            self.action_save_layout()
            event.stop()

    def _refresh_widgets_from_cache(self) -> None:
        """Refresh mounted widgets after a layout recompose without collecting new data."""
        if self._last_reading is None:
            return

        with contextlib.suppress(Exception):
            self._update_all_widgets(self._last_reading)

    def action_toggle_layout(self) -> None:
        """Toggle between side-by-side and stacked summary layouts."""
        next_mode = "stacked" if self._runtime_layout.summary_mode == "side_by_side" else "side_by_side"
        self._runtime_layout = replace(self._runtime_layout, summary_mode=next_mode)
        self.refresh(recompose=True)
        self.call_after_refresh(self._refresh_widgets_from_cache)
        self.notify(f"Layout changed to {next_mode}", timeout=2)

    def action_save_layout(self) -> None:
        """Save the current runtime layout to the config file."""
        try:
            config_path = config_loader.save_layout_config(self._runtime_layout)
        except Exception as e:
            self.notify(f"Failed to save layout: {e}", severity="error", timeout=5)
            return

        self.config = replace(self.config, layout=replace(self._runtime_layout))
        self.notify(f"Saved layout to {config_path}", timeout=3)

    def on_mount(self) -> None:
        """Start background data collection when app mounts."""
        # Start periodic data collection
        self._collector_task = asyncio.create_task(self._collection_loop())

        # Initial data load
        self.refresh_all_data()

    async def on_unmount(self) -> None:
        """Clean up when app unmounts."""
        if self._collector_task:
            self._collector_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._collector_task

        # Close database resources
        self.database.close()

    async def _collection_loop(self) -> None:
        """Background loop for periodic power data collection.

        Runs every collection_interval seconds, collecting data and updating UI.
        """
        while True:
            try:
                await asyncio.sleep(self.config.collection_interval)
                await self._collect_and_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.notify(f"Collection error: {e}", severity="error", timeout=5)

    async def _collect_and_update(self) -> None:
        """Collect power data and update all widgets.

        Runs in executor to avoid blocking the UI thread.
        """
        try:
            # Run blocking collector in executor
            loop = asyncio.get_event_loop()
            reading = await loop.run_in_executor(None, self.collector.collect)

            # Try to save to database, but continue updating UI even if it fails
            try:
                await loop.run_in_executor(None, self.database.insert_reading, reading)
            except Exception as db_error:
                self.notify(
                    f"Warning: Failed to save reading to database: {db_error}",
                    severity="warning",
                    timeout=3,
                )

            # Update all widgets (already on main thread after await)
            self._update_all_widgets(reading)

        except Exception as e:
            self.notify(f"Failed to collect data: {e}", severity="error", timeout=5)

    def _update_all_widgets(self, reading: PowerReading) -> None:
        """Update all widgets with new data.

        Args:
            reading: Latest PowerReading
        """
        self._last_reading = reading

        # Update live data panel
        live_panel = self.query_one("#live-data", LiveDataPanel)
        live_panel.update_reading(reading)

        # Update statistics panel
        stats = self.database.get_statistics(limit=self.config.stats_history_limit)
        stats_panel = self.query_one("#stats", StatsPanel)
        stats_panel.update_stats(stats)

        # Update chart with last 60 readings
        history = self.database.query_history(limit=self.config.chart_history_limit)
        chart = self.query_one("#chart", ChartWidget)
        chart.update_chart(history)

    def refresh_all_data(self) -> None:
        """Force refresh all data (for 'r' key binding)."""
        try:
            reading = self.collector.collect()

            # Try to save to database, but continue even if it fails
            try:
                self.database.insert_reading(reading)
            except Exception as db_error:
                self.notify(
                    f"Warning: Failed to save reading: {db_error}",
                    severity="warning",
                    timeout=3,
                )

            self._update_all_widgets(reading)
            self.notify("Data refreshed", timeout=2)
        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error", timeout=5)

    def action_refresh(self) -> None:
        """Handle refresh key binding (R)."""
        self.run_worker(self._async_refresh, exclusive=True)

    async def _async_refresh(self) -> None:
        """Async refresh worker."""
        await self._collect_and_update()
        self.notify("Data refreshed", timeout=2)

    def action_clear_history(self) -> None:
        """Handle clear history key binding (C).

        Clears all historical readings from database.
        """
        rows_deleted = self.database.clear_history()
        self.notify(f"Cleared {rows_deleted} historical readings", timeout=3)
        # Refresh display
        self.refresh_all_data()

    async def action_quit(self) -> None:
        """Handle quit action (Q or ESC).

        Ensures background collection task is cancelled cleanly
        and any in-flight data is saved before exiting.
        """
        # Show shutting down notification
        self.notify("Shutting down...", timeout=1)

        # Cancel collection task if it's running
        if self._collector_task and not self._collector_task.done():
            self._collector_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._collector_task

        # Give any pending database writes a moment to complete
        # (executor tasks may still be running)
        await asyncio.sleep(0.1)

        # Close database resources
        self.database.close()

        # Now safe to exit
        self.exit()
