"""
Transition prompt dialog for asking users if now is a good time to categorize.

Uses tkinter for cross-platform GUI dialog.
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional

# Module-level singleton tracking
_popup_lock = threading.Lock()
_popup_active = False
_popup_instance: Optional["TransitionPrompt"] = None


def is_popup_showing() -> bool:
    """Check if a popup is currently being displayed."""
    with _popup_lock:
        return _popup_active


def close_active_popup():
    """Close the currently active popup if one exists."""
    with _popup_lock:
        if _popup_instance and _popup_instance.root:
            try:
                _popup_instance.root.after(0, _popup_instance._force_close)
            except Exception:
                pass


class TransitionPrompt:
    """Prompt dialog asking user if now is a good time to categorize."""

    RESPONSES = {
        "free": "Yes, I'm free",
        "break": "No, I'm on break.",
        "interrupting": "No, I'm working.",
        "dismiss": "Not now, ask later."
    }

    # Auto-close popup after this many seconds of user inactivity
    IDLE_AUTO_CLOSE_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.response: Optional[str] = None
        self.root: Optional[tk.Tk] = None
        self._idle_check_id: Optional[str] = None
        self._closed = False

    def show(self, transition_type: str = None) -> Optional[str]:
        """
        Show prompt dialog and return user's response.

        Args:
            transition_type: Type of transition detected (for context)

        Returns:
            Response key ("free", "break", "interrupting", "dismiss", "auto_closed") or None
        """
        global _popup_active, _popup_instance

        # Check if popup already showing - prevent duplicates
        with _popup_lock:
            if _popup_active:
                return None
            _popup_active = True
            _popup_instance = self

        try:
            self.root = tk.Tk()
            self.root.title("SyncoPaid - Time Categorization")
            self.root.attributes('-topmost', True)

            # Set minimum width, let height auto-size to fit content
            self.root.minsize(400, 0)
            # Prevent horizontal resizing but allow vertical auto-sizing
            self.root.resizable(False, False)

            # Handle window close button (X)
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

            # Message
            msg = "Is now a good time to categorize your time?"
            if transition_type:
                msg += f"\n\n(Detected: {transition_type.replace('_', ' ').title()})"

            label = tk.Label(self.root, text=msg, font=('Segoe UI', 10), pady=20)
            label.pack()

            # Response buttons
            btn_frame = tk.Frame(self.root)
            btn_frame.pack(pady=(10, 20))  # Extra bottom padding for last button

            for key, text in self.RESPONSES.items():
                btn = tk.Button(
                    btn_frame,
                    text=text,
                    command=lambda k=key: self._handle_response(k),
                    width=20
                )
                btn.pack(pady=5)

            # Start idle monitoring for auto-close
            self._start_idle_monitoring()

            self.root.mainloop()
            return self.response

        finally:
            # Clean up singleton tracking
            with _popup_lock:
                _popup_active = False
                _popup_instance = None

    def _handle_response(self, response_key: str):
        """Handle button click."""
        if self._closed:
            return
        self._closed = True
        self.response = response_key
        self._cancel_idle_monitoring()
        self.root.destroy()

    def _on_window_close(self):
        """Handle window close button (X) click."""
        self._handle_response("dismiss")

    def _start_idle_monitoring(self):
        """Start periodic idle time checking for auto-close."""
        # Check every 10 seconds
        self._check_idle()

    def _check_idle(self):
        """Check idle time and auto-close if user has been idle too long."""
        if self._closed or not self.root:
            return

        try:
            from syncopaid.tracker_windows_idle import get_idle_seconds
            idle_seconds = get_idle_seconds()

            if idle_seconds >= self.IDLE_AUTO_CLOSE_SECONDS:
                # User has been idle for 5+ minutes, auto-close
                self._auto_close()
                return

            # Schedule next check in 10 seconds
            self._idle_check_id = self.root.after(10000, self._check_idle)

        except Exception:
            # If idle detection fails, continue without auto-close
            self._idle_check_id = self.root.after(10000, self._check_idle)

    def _cancel_idle_monitoring(self):
        """Cancel the idle monitoring timer."""
        if self._idle_check_id and self.root:
            try:
                self.root.after_cancel(self._idle_check_id)
            except Exception:
                pass
        self._idle_check_id = None

    def _auto_close(self):
        """Auto-close the popup due to user inactivity."""
        if self._closed:
            return
        self._closed = True
        self.response = "auto_closed"
        self._cancel_idle_monitoring()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _force_close(self):
        """Force close the popup (called externally)."""
        self._auto_close()
