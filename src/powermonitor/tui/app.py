"""powermonitor Textual TUI Application - auto-updating power monitoring interface."""

import asyncio
import contextlib
from typing import Protocol

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.events import Resize
from textual.widgets import Footer
from textual.widgets import Header

from ..collector import default_collector
from ..collector.base import PowerCollector
from ..config import PowerMonitorConfig
from ..database import Database
from ..models import PowerReading
from .layout import TUILayoutMode
from .layout import select_tui_layout
from .widgets import ChartWidget
from .widgets import LiveDataPanel
from .widgets import StatsPanel


class PowerDataStore(Protocol):
    """Persistence operations used by the TUI."""

    def insert_reading(self, reading: PowerReading) -> int:
        """Store a power reading and return its row ID."""
        ...

    def query_history(self, limit: int | None = 20) -> list[PowerReading]:
        """Return recent power readings."""
        ...

    def get_statistics(self, limit: int | None = 100) -> dict:
        """Return aggregate statistics for recent power readings."""
        ...

    def clear_history(self) -> int:
        """Delete stored readings and return the deleted row count."""
        ...

    def close(self) -> None:
        """Close database resources."""
        ...


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

    #summary-row {
        margin: 1 1 0 1;
    }

    #layout-root {
        layout: vertical;
        height: 1fr;
    }

    #layout-root.stacked #summary-row {
        layout: vertical;
        height: 22;
    }

    #layout-root.side-by-side #summary-row {
        layout: horizontal;
        height: 10;
    }

    #layout-root.compact-stacked #summary-row {
        layout: vertical;
        height: 14;
    }

    #live-data {
        width: 1fr;
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    #layout-root.side-by-side #live-data {
        margin: 0 1 0 0;
    }

    #layout-root.stacked #live-data,
    #layout-root.compact-stacked #live-data {
        margin: 0 0 1 0;
    }

    #stats {
        width: 1fr;
        height: 1fr;
        border: solid cyan;
        padding: 1;
    }

    #chart {
        height: 1fr;
        border: solid blue;
        padding: 1;
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("escape", "quit", "Quit", show=False),
        Binding("c", "clear_history", "Clear History", key_display="C"),
    ]

    TITLE = "powermonitor - macOS Power Monitoring"

    def __init__(
        self,
        config: PowerMonitorConfig | None = None,
        collector: PowerCollector | None = None,
        database: PowerDataStore | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or PowerMonitorConfig()
        self.collector = collector if collector is not None else default_collector()
        self.database = database if database is not None else Database(self.config.database_path)
        self._collector_task: asyncio.Task | None = None
        self._layout_mode = TUILayoutMode.COMPACT_STACKED

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        self._layout_mode = select_tui_layout(self.size)
        yield Header()
        yield Container(
            Container(
                LiveDataPanel(id="live-data"),
                StatsPanel(id="stats"),
                id="summary-row",
            ),
            ChartWidget(id="chart"),
            id="layout-root",
            classes=self._layout_mode.value,
        )
        yield Footer()

    def on_mount(self) -> None:
        """Start background data collection when app mounts."""
        self._apply_layout_mode(select_tui_layout(self.size))

        # Start periodic data collection
        self._collector_task = asyncio.create_task(self._collection_loop())

        # Initial data load
        self.refresh_all_data()

    def on_resize(self, event: Resize) -> None:
        """Adapt layout when the terminal size crosses a layout threshold."""
        self._apply_layout_mode(select_tui_layout(event.size))

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

    def _apply_layout_mode(self, layout_mode: TUILayoutMode) -> None:
        """Apply a layout mode without replacing mounted widgets."""
        if layout_mode == self._layout_mode:
            return

        try:
            layout_root = self.query_one("#layout-root", Container)
        except NoMatches:
            self._layout_mode = layout_mode
            return

        for existing_mode in TUILayoutMode:
            layout_root.remove_class(existing_mode.value)
        layout_root.add_class(layout_mode.value)
        self._layout_mode = layout_mode
        layout_root.refresh(layout=True)

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
