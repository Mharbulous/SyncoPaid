"""
Event handlers for action-based screenshot capture.

Handles mouse clicks, keyboard events, drag detection, and window focus changes.
"""

import logging
import threading
import time
from typing import Optional, Callable

try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except ImportError as e:
    PYNPUT_AVAILABLE = False
    logging.warning(f"pynput import failed: {e}. Action screenshots will be disabled.")

try:
    import win32gui
    WIN32GUI_AVAILABLE = True
except ImportError:
    WIN32GUI_AVAILABLE = False


class ActionEventHandler:
    """
    Handles mouse and keyboard events for action screenshot capture.

    Manages:
    - Mouse clicks and drag detection
    - Enter key presses
    - Window focus changes
    - Event throttling and statistics
    """

    def __init__(
        self,
        capture_callback: Callable[[str], None],
        throttle_seconds: float = 0.5
    ):
        """
        Initialize the event handler.

        Args:
            capture_callback: Function to call when action detected (receives action type)
            throttle_seconds: Minimum seconds between captures
        """
        self.capture_callback = capture_callback
        self.throttle_seconds = throttle_seconds

        # Drag tracking state
        self.is_dragging = False
        self.drag_start_button = None
        self.drag_start_pos = None

        # Throttling state
        self.last_capture_time: float = 0
        self.capture_lock = threading.Lock()

        # Statistics
        self.total_click_captures = 0
        self.total_enter_captures = 0
        self.total_drag_start_captures = 0
        self.total_drag_end_captures = 0
        self.total_focus_captures = 0
        self.total_throttled = 0

        # Event listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Focus change monitoring
        self.last_focus_hwnd: Optional[int] = None
        self.focus_monitor_thread: Optional[threading.Thread] = None
        self.focus_monitor_running = False
        self.focus_poll_interval = 0.5  # Poll every 500ms

    def start(self):
        """Start listening for user actions."""
        if not PYNPUT_AVAILABLE:
            logging.warning("pynput not available, cannot start event listeners")
            return

        try:
            # Start mouse listener
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_move=self._on_mouse_move
            )
            self.mouse_listener.start()

            # Start keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            self.keyboard_listener.start()

            # Start focus change monitor
            if WIN32GUI_AVAILABLE:
                self.focus_monitor_running = True
                self.focus_monitor_thread = threading.Thread(
                    target=self._monitor_focus_changes,
                    daemon=True,
                    name='focus_monitor'
                )
                self.focus_monitor_thread.start()

            logging.info(f"Action event listeners started (throttle: {self.throttle_seconds}s)")
        except Exception as e:
            logging.error(f"Failed to start event listeners: {e}", exc_info=True)

    def stop(self):
        """Stop listening for user actions."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.focus_monitor_thread:
            self.focus_monitor_running = False
            self.focus_monitor_thread.join(timeout=2.0)
            self.focus_monitor_thread = None

        logging.info("Action event listeners stopped")

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        try:
            if pressed:
                # Mouse button down - track for potential drag detection
                self.drag_start_button = button
                self.drag_start_pos = (x, y)
            else:
                # Mouse button up - either click or drop
                if self.is_dragging:
                    # This is a drag end (drop)
                    self.is_dragging = False
                    self.drag_start_button = None
                    self.drag_start_pos = None
                    logging.info("Action detected: drop")
                    self._trigger_capture('drop')
                else:
                    # Regular click
                    self.drag_start_button = None
                    self.drag_start_pos = None
                    logging.info("Action detected: click")
                    self._trigger_capture('click')
        except Exception as e:
            logging.error(f"Error in mouse click handler: {e}", exc_info=True)

    def _on_mouse_move(self, x, y):
        """Handle mouse move events to detect drag operations."""
        # Detect drag start: button is held and mouse moved significantly
        if self.drag_start_button is not None and not self.is_dragging:
            if self.drag_start_pos is not None:
                # Check if moved more than 10 pixels (threshold to distinguish drag from click)
                dx = abs(x - self.drag_start_pos[0])
                dy = abs(y - self.drag_start_pos[1])
                if dx > 10 or dy > 10:
                    # This is a drag start
                    self.is_dragging = True
                    self._trigger_capture('drag')

    def _on_key_press(self, key):
        """Handle keyboard press events."""
        try:
            # Check if Enter/Return key was pressed
            if key == keyboard.Key.enter:
                self._trigger_capture('enter')
        except AttributeError:
            # Some keys don't have all attributes
            pass
        except Exception as e:
            logging.error(f"Error in key press handler: {e}")

    def _monitor_focus_changes(self):
        """Background thread to detect window focus changes."""
        if not WIN32GUI_AVAILABLE:
            return

        while self.focus_monitor_running:
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd and current_hwnd != self.last_focus_hwnd:
                    if self.last_focus_hwnd is not None:
                        # Focus changed - capture screenshot
                        logging.info(
                            f"Action detected: focus change "
                            f"({self.last_focus_hwnd} -> {current_hwnd})"
                        )
                        self._trigger_capture('focus')
                    self.last_focus_hwnd = current_hwnd
            except Exception as e:
                logging.debug(f"Error in focus monitor: {e}")
            time.sleep(self.focus_poll_interval)

    def _trigger_capture(self, action: str):
        """
        Trigger a screenshot capture with throttling.

        Args:
            action: The action type ('click', 'enter', 'drag', 'drop', 'focus')
        """
        # Check throttling
        with self.capture_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_capture_time

            if time_since_last < self.throttle_seconds:
                self.total_throttled += 1
                logging.info(f"Throttled {action} ({time_since_last:.2f}s since last)")
                return

            self.last_capture_time = current_time

        # Update statistics
        if action == 'click':
            self.total_click_captures += 1
        elif action == 'enter':
            self.total_enter_captures += 1
        elif action == 'drag':
            self.total_drag_start_captures += 1
        elif action == 'drop':
            self.total_drag_end_captures += 1
        elif action == 'focus':
            self.total_focus_captures += 1

        # Trigger the callback
        self.capture_callback(action)

    def get_stats(self) -> dict:
        """Get event capture statistics."""
        return {
            'click_captures': self.total_click_captures,
            'enter_captures': self.total_enter_captures,
            'drag_start_captures': self.total_drag_start_captures,
            'drag_end_captures': self.total_drag_end_captures,
            'focus_captures': self.total_focus_captures,
            'throttled': self.total_throttled
        }
