"""
Click event recorder module.

Records left mouse clicks as ActivityEvents in the database.
Each click creates an event with:
- app: "SyncoPaid.exe"
- title: "SyncoPaid Stopwatch reset"
- duration_seconds: 1.0
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Callable

from syncopaid.tracker_state import ActivityEvent, STATE_ACTIVE

try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError as e:
    PYNPUT_AVAILABLE = False
    logging.warning(f"pynput import failed: {e}. Click recording will be disabled.")


class ClickRecorder:
    """
    Records left mouse clicks as ActivityEvents.

    Each left click creates an ActivityEvent with:
    - app: "SyncoPaid.exe"
    - title: "SyncoPaid Stopwatch reset"
    - duration_seconds: 1.0
    - timestamp: current time in ISO8601 format
    """

    # Constants for click events
    CLICK_APP = "SyncoPaid.exe"
    CLICK_TITLE = "SyncoPaid Stopwatch reset"
    CLICK_DURATION = 1.0

    def __init__(
        self,
        event_callback: Callable[[ActivityEvent], None],
        enabled: bool = True
    ):
        """
        Initialize the click recorder.

        Args:
            event_callback: Function to call with each click ActivityEvent
            enabled: Whether click recording is enabled (default: True)
        """
        self.event_callback = event_callback
        self.enabled = enabled

        # Mouse listener
        self.mouse_listener: Optional[mouse.Listener] = None

        # Statistics
        self.total_clicks = 0
        self.stats_lock = threading.Lock()

        if self.enabled:
            logging.info("ClickRecorder initialized")
        else:
            logging.info("ClickRecorder disabled")

    def start(self):
        """Start listening for left mouse clicks."""
        if not self.enabled:
            logging.info("Click recording disabled, not starting listener")
            return

        if not PYNPUT_AVAILABLE:
            logging.warning("pynput not available, cannot start click recorder")
            return

        try:
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click
            )
            self.mouse_listener.start()
            logging.info("ClickRecorder started - listening for left clicks")
        except Exception as e:
            logging.error(f"Failed to start click recorder: {e}", exc_info=True)

    def stop(self):
        """Stop listening for mouse clicks."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            logging.info(f"ClickRecorder stopped. Total clicks recorded: {self.total_clicks}")

    def _on_mouse_click(self, x, y, button, pressed):
        """
        Handle mouse click events.

        Only records left button releases (completed clicks).
        """
        try:
            # Only record left button releases (completed clicks)
            if button == mouse.Button.left and not pressed:
                self._record_click()
        except Exception as e:
            logging.error(f"Error in click handler: {e}", exc_info=True)

    def _record_click(self):
        """Create and emit an ActivityEvent for the click."""
        # Generate timestamp in ISO8601 format with timezone
        timestamp = datetime.now(timezone.utc).isoformat()

        # Calculate end time (1 second after start)
        end_time = datetime.now(timezone.utc)
        end_time_str = end_time.isoformat()

        # Create the ActivityEvent
        event = ActivityEvent(
            timestamp=timestamp,
            duration_seconds=self.CLICK_DURATION,
            app=self.CLICK_APP,
            title=self.CLICK_TITLE,
            end_time=end_time_str,
            url=None,
            cmdline=None,
            is_idle=False,
            state=STATE_ACTIVE,
            interaction_level="clicking",
            metadata={"event_type": "click"}
        )

        # Update statistics
        with self.stats_lock:
            self.total_clicks += 1

        # Emit the event via callback
        try:
            self.event_callback(event)
            logging.debug(f"Click event recorded: {timestamp}")
        except Exception as e:
            logging.error(f"Error emitting click event: {e}", exc_info=True)

    def get_stats(self) -> dict:
        """Get click recording statistics."""
        with self.stats_lock:
            return {
                'total_clicks': self.total_clicks
            }


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Click Recorder module test")
    print(f"pynput available: {PYNPUT_AVAILABLE}")

    if PYNPUT_AVAILABLE:
        print("\nStarting click recorder test...")
        print("Left-click to generate events")
        print("Press Ctrl+C to stop\n")

        # Create test callback
        def test_callback(event: ActivityEvent):
            print(f"Click Event: app={event.app}, title={event.title}, "
                  f"duration={event.duration_seconds}s, timestamp={event.timestamp[:19]}")

        recorder = ClickRecorder(
            event_callback=test_callback,
            enabled=True
        )

        # Start recording
        recorder.start()

        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping test...")
            recorder.stop()
            print(f"\n✓ Test complete")
            print(f"Stats: {recorder.get_stats()}")
    else:
        print("\n⚠ Cannot test: pynput not available")
