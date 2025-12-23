"""Tooltip widget for tkinter."""
import tkinter as tk


class ToolTip:
    """Simple tooltip for tkinter widgets."""

    def __init__(self, widget, text_func):
        """
        Create tooltip that shows text from text_func on hover.

        Args:
            widget: Widget to attach tooltip to
            text_func: Callable that returns tooltip text (receives event)
        """
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None

        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)
        widget.bind('<Motion>', self._update_position)

    def _show(self, event):
        text = self.text_func(event)
        if not text:
            return

        x = event.x_root + 10
        y = event.y_root + 10

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", 9)
        )
        label.pack()

    def _hide(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def _update_position(self, event):
        if self.tip_window:
            self._hide(event)
            self._show(event)
