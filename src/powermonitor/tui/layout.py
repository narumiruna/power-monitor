"""Interactive layout helpers for the powermonitor TUI."""

from typing import Literal

from textual import events
from textual.message import Message
from textual.widgets import Static

ResizeAxis = Literal["x", "y"]
ResizeTarget = Literal["live_stats", "summary_chart", "stacked_live_stats", "stacked_stats_chart"]


class LayoutResizeHandle(Static):
    """Mouse-draggable handle that emits resize deltas."""

    DEFAULT_CSS = """
    LayoutResizeHandle {
        background: $accent;
        color: $text;
    }
    """

    class Resized(Message):
        """Emitted when a drag changes the handle position."""

        def __init__(self, handle: "LayoutResizeHandle", target: ResizeTarget, axis: ResizeAxis, delta: int) -> None:
            super().__init__()
            self.handle = handle
            self.target = target
            self.axis = axis
            self.delta = delta

    def __init__(
        self,
        *,
        target: ResizeTarget,
        axis: ResizeAxis,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__("", id=id, classes=classes)
        self.target = target
        self.axis = axis
        self._dragging = False
        self._last_screen_position = 0

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Start resizing and capture mouse movement."""
        if event.button != 1:
            return

        self._dragging = True
        self._last_screen_position = event.screen_x if self.axis == "x" else event.screen_y
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Emit a resize delta while dragging."""
        if not self._dragging:
            return

        screen_position = event.screen_x if self.axis == "x" else event.screen_y
        delta = screen_position - self._last_screen_position
        if delta == 0:
            return

        self._last_screen_position = screen_position
        self.post_message(self.Resized(self, self.target, self.axis, delta))
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Stop resizing and release mouse capture."""
        if not self._dragging:
            return

        self._dragging = False
        self.release_mouse()
        event.stop()
