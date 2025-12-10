"""
Action-based screenshot capture module.

Captures screenshots when user performs specific actions:
- Mouse clicks
- Enter/Return key presses
- Drag start operations
- Drag end (drop) operations
- Window focus changes (Alt+Tab, taskbar clicks, etc.)

Screenshots are saved to screenshots/actions/ with format:
YYYY-MM-DD_HH-mm-dd_UTC_{action}.jpg
"""

import os
import sys
import logging
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL regardless of platform (needed for type hints)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    PIL_AVAILABLE = False
    logging.warning(f"PIL import failed: {e}. Action screenshots will be disabled.")
    class Image:
        class Image:
            pass

if WINDOWS:
    try:
        import win32gui
        from PIL import ImageGrab
        WINDOWS_APIS_AVAILABLE = PIL_AVAILABLE and True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Screenshot APIs not available. Install pywin32, Pillow.")
else:
    WINDOWS_APIS_AVAILABLE = False

# Import pynput for keyboard/mouse event listening
try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except ImportError as e:
    PYNPUT_AVAILABLE = False
    logging.warning(f"pynput import failed: {e}. Action screenshots will be disabled.")


# Apps to skip screenshot capture
SKIP_APPS = {
    'LockApp.exe',
    'ScreenSaver.scr',
    'LogonUI.exe'
}


class ActionScreenshotWorker:
    """
    Worker class for action-based screenshot capture.

    Listens for user actions (clicks, enter key, drag operations) and
    captures screenshots asynchronously. Uses pynput for event listening
    and ThreadPoolExecutor for non-blocking capture.
    """

    def __init__(
        self,
        screenshot_dir: Path,
        db_insert_callback,
        quality: int = 65,
        max_dimension: int = 1920,
        throttle_seconds: float = 0.5,
        enabled: bool = True
    ):
        """
        Initialize the action screenshot worker.

        Args:
            screenshot_dir: Base directory for storing action screenshots
            db_insert_callback: Function to call for inserting screenshot records
            quality: JPEG quality 1-100 (default: 65)
            max_dimension: Max width/height in pixels (default: 1920)
            throttle_seconds: Minimum seconds between screenshots (default: 0.5)
            enabled: Whether action screenshots are enabled (default: True)
        """
        self.screenshot_dir = screenshot_dir
        self.db_insert_callback = db_insert_callback
        self.quality = quality
        self.max_dimension = max_dimension
        self.throttle_seconds = throttle_seconds
        self.enabled = enabled

        # Thread pool for async capture
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='action_screenshot')

        # Throttling state
        self.last_capture_time: float = 0
        self.capture_lock = threading.Lock()

        # Drag tracking state
        self.is_dragging = False
        self.drag_start_button = None
        self.drag_start_pos = None

        # Statistics
        self.total_click_captures = 0
        self.total_enter_captures = 0
        self.total_drag_start_captures = 0
        self.total_drag_end_captures = 0
        self.total_focus_captures = 0
        self.total_throttled = 0

        # Event listeners (will be set by start())
        self.mouse_listener = None
        self.keyboard_listener = None

        # Focus change monitoring
        self.last_focus_hwnd: Optional[int] = None
        self.focus_monitor_thread: Optional[threading.Thread] = None
        self.focus_monitor_running = False
        self.focus_poll_interval = 0.5  # Poll every 500ms

        # Ensure screenshot directory exists
        if self.enabled:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"ActionScreenshotWorker initialized: {screenshot_dir}")
        else:
            logging.info("ActionScreenshotWorker disabled")

    def start(self):
        """Start listening for user actions."""
        if not self.enabled:
            logging.info("Action screenshots disabled, not starting listeners")
            return

        if not PYNPUT_AVAILABLE:
            logging.warning("pynput not available, cannot start action screenshot listeners")
            return

        if not WINDOWS_APIS_AVAILABLE:
            logging.warning("Windows APIs not available, cannot start action screenshot listeners")
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
            self.focus_monitor_running = True
            self.focus_monitor_thread = threading.Thread(
                target=self._monitor_focus_changes,
                daemon=True,
                name='focus_monitor'
            )
            self.focus_monitor_thread.start()

            logging.info(
                f"Action screenshot listeners started. "
                f"Screenshot dir: {self.screenshot_dir}, "
                f"throttle: {self.throttle_seconds}s"
            )
        except Exception as e:
            logging.error(f"Failed to start action screenshot listeners: {e}", exc_info=True)

    def stop(self):
        """Stop listening for user actions."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        # Stop focus monitor thread
        if self.focus_monitor_thread:
            self.focus_monitor_running = False
            self.focus_monitor_thread.join(timeout=2.0)
            self.focus_monitor_thread = None

        logging.info("Action screenshot listeners stopped")

    def _on_mouse_click(self, x, y, button, pressed):
        """
        Handle mouse click events.

        Args:
            x, y: Mouse position
            button: Mouse button (left, right, middle)
            pressed: True if pressed, False if released
        """
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
                    logging.info("Action screenshot: drop detected")
                    self._capture_action_screenshot('drop')
                else:
                    # Regular click
                    self.drag_start_button = None
                    self.drag_start_pos = None
                    logging.info("Action screenshot: click detected")
                    self._capture_action_screenshot('click')
        except Exception as e:
            logging.error(f"Error in mouse click handler: {e}", exc_info=True)

    def _on_mouse_move(self, x, y):
        """
        Handle mouse move events to detect drag operations.

        Args:
            x, y: Mouse position
        """
        # Detect drag start: button is held and mouse moved significantly
        if self.drag_start_button is not None and not self.is_dragging:
            if self.drag_start_pos is not None:
                # Check if moved more than 10 pixels (threshold to distinguish drag from click)
                dx = abs(x - self.drag_start_pos[0])
                dy = abs(y - self.drag_start_pos[1])
                if dx > 10 or dy > 10:
                    # This is a drag start
                    self.is_dragging = True
                    self._capture_action_screenshot('drag')

    def _on_key_press(self, key):
        """
        Handle keyboard press events.

        Args:
            key: The key that was pressed
        """
        try:
            # Check if Enter/Return key was pressed
            if key == keyboard.Key.enter:
                self._capture_action_screenshot('enter')
        except AttributeError:
            # Some keys don't have all attributes
            pass
        except Exception as e:
            logging.error(f"Error in key press handler: {e}")

    def _monitor_focus_changes(self):
        """Background thread to detect window focus changes."""
        while self.focus_monitor_running:
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd and current_hwnd != self.last_focus_hwnd:
                    if self.last_focus_hwnd is not None:
                        # Focus changed - capture screenshot
                        logging.info(f"Action screenshot: focus change detected ({self.last_focus_hwnd} -> {current_hwnd})")
                        self._capture_action_screenshot('focus')
                    self.last_focus_hwnd = current_hwnd
            except Exception as e:
                logging.debug(f"Error in focus monitor: {e}")
            time.sleep(self.focus_poll_interval)

    def _capture_action_screenshot(self, action: str):
        """
        Capture a screenshot for the specified action.

        Args:
            action: The action type ('click', 'enter', 'drag', 'drop', 'focus')
        """
        if not WINDOWS_APIS_AVAILABLE:
            logging.warning("Windows APIs not available, skipping action screenshot")
            return

        # CRITICAL: Capture hwnd immediately in the callback thread, not in the worker thread
        # By the time the worker thread runs, the foreground window may have changed
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                logging.warning(f"No foreground window for {action} screenshot")
                return
            logging.info(f"Action screenshot: captured hwnd={hwnd} for {action}")
        except Exception as e:
            logging.error(f"Failed to get foreground window for {action}: {e}", exc_info=True)
            return

        # Check throttling
        with self.capture_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_capture_time

            if time_since_last < self.throttle_seconds:
                self.total_throttled += 1
                logging.info(f"Throttled {action} screenshot ({time_since_last:.2f}s since last)")
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

        # Submit to thread pool with hwnd captured now
        logging.info(f"Submitting {action} screenshot capture for hwnd {hwnd}")
        self.executor.submit(self._capture_and_save, action, hwnd)

    def _capture_and_save(self, action: str, hwnd: int):
        """
        Capture screenshot and save to disk (runs in worker thread).

        Args:
            action: The action type ('click', 'enter', 'drag', 'drop', 'focus')
            hwnd: Window handle captured at event time
        """
        try:
            # Get window info for metadata
            window_app = None
            window_title = None
            try:
                import win32process
                import psutil

                window_title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                # Handle signed/unsigned integer overflow
                if pid < 0:
                    pid = pid + 2**32

                try:
                    process = psutil.Process(pid)
                    window_app = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    window_app = None

            except Exception as e:
                logging.debug(f"Error getting window info: {e}")

            # Skip certain apps
            if window_app in SKIP_APPS:
                logging.debug(f"Skipping screenshot: {window_app}")
                return

            # Capture the screenshot
            img = self._capture_window(hwnd)
            if img is None:
                logging.warning(f"Screenshot capture failed for {action} action (hwnd={hwnd})")
                return

            logging.info(f"Action screenshot: captured image {img.size[0]}x{img.size[1]} for {action}")

            # Resize if needed
            img = self._resize_if_needed(img)

            # Generate timestamp (use local timezone, consistent with periodic screenshots)
            timestamp = datetime.now().astimezone().isoformat()

            # Generate file path
            file_path = self._get_screenshot_path(timestamp, action)

            # Save image as JPEG
            logging.info(f"Saving {action} screenshot to: {file_path}")
            img.save(str(file_path), 'JPEG', quality=self.quality, optimize=True)

            # Insert into database
            self.db_insert_callback(
                captured_at=timestamp,
                file_path=str(file_path),
                window_app=window_app,
                window_title=window_title,
                dhash=None  # No deduplication for action screenshots
            )

            logging.info(f"Saved {action} screenshot: {file_path.name}")

        except Exception as e:
            logging.error(f"Error capturing {action} screenshot: {e}", exc_info=True)

    def _capture_window(self, hwnd: int) -> Optional[Image.Image]:
        """
        Capture screenshot of the specified window.

        Args:
            hwnd: Windows window handle

        Returns:
            PIL Image or None if capture failed
        """
        if not WINDOWS_APIS_AVAILABLE:
            return None

        try:
            # Validate window
            if not win32gui.IsWindow(hwnd):
                return None

            if not win32gui.IsWindowVisible(hwnd):
                return None

            if win32gui.IsIconic(hwnd):
                return None

            # Get window rectangle
            rect = win32gui.GetWindowRect(hwnd)
            x1, y1, x2, y2 = rect
            width = x2 - x1
            height = y2 - y1

            # Validate dimensions
            if width <= 0 or height <= 0:
                return None

            if width > 10000 or height > 10000:
                return None

            # Check if completely off-screen
            if x2 < 0 or y2 < 0:
                return None

            # Capture the screenshot
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            return img

        except Exception as e:
            logging.error(f"Error capturing window: {e}")
            return None

    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Resize image if either dimension exceeds max_dimension.

        Args:
            img: PIL Image

        Returns:
            Resized PIL Image (or original if no resize needed)
        """
        width, height = img.size
        max_dim = max(width, height)

        if max_dim <= self.max_dimension:
            return img

        # Calculate new dimensions maintaining aspect ratio
        scale = self.max_dimension / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _get_screenshot_path(self, timestamp: str, action: str) -> Path:
        """
        Generate file path for action screenshot.

        Format: {screenshot_dir}/YYYY-MM-DD/YYYY-MM-DD_HH-mm-ss_UTC_{action}.jpg
        Examples:
            - 2025-12-10/2025-12-10_00-33-30_UTC-08-00_click.jpg
            - 2025-12-10/2025-12-10_14-22-15_UTC-08-00_enter.jpg
            - 2025-12-10/2025-12-10_14-22-15_UTC-08-00_focus.jpg

        Args:
            timestamp: ISO timestamp with timezone information
            action: Action type ('click', 'enter', 'drag', 'drop', 'focus')

        Returns:
            Path object for screenshot file
        """
        dt = datetime.fromisoformat(timestamp)

        # Create date-based subdirectory (local date)
        date_dir = self.screenshot_dir / dt.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with date, time, and timezone
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H-%M-%S')
        tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", "EST", or "UTC-08:00", etc.

        # Sanitize timezone for Windows filenames (remove colons)
        # "UTC-08:00" -> "UTC-08-00", "PST" -> "PST"
        tz_abbr = tz_abbr.replace(':', '-')

        filename = f"{date_str}_{time_str}_{tz_abbr}_{action}.jpg"
        return date_dir / filename

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the action screenshot worker.

        Args:
            wait: Whether to wait for pending tasks
            timeout: Max seconds to wait
        """
        # Stop listeners first
        self.stop()

        logging.info(
            f"ActionScreenshotWorker shutting down. "
            f"Stats: clicks={self.total_click_captures}, "
            f"enters={self.total_enter_captures}, "
            f"drag_starts={self.total_drag_start_captures}, "
            f"drag_ends={self.total_drag_end_captures}, "
            f"focus={self.total_focus_captures}, "
            f"throttled={self.total_throttled}"
        )

        # Shutdown thread pool
        self.executor.shutdown(wait=wait, cancel_futures=not wait)

    def get_stats(self) -> dict:
        """Get action screenshot capture statistics."""
        return {
            'click_captures': self.total_click_captures,
            'enter_captures': self.total_enter_captures,
            'drag_start_captures': self.total_drag_start_captures,
            'drag_end_captures': self.total_drag_end_captures,
            'focus_captures': self.total_focus_captures,
            'throttled': self.total_throttled
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_action_screenshot_directory() -> Path:
    """
    Get the default action screenshot storage directory.

    Returns:
        Path to action screenshot directory
    """
    import sys
    import os

    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        screenshot_dir = appdata / 'TimeLawg' / 'screenshots' / 'actions'
    else:
        screenshot_dir = Path.home() / '.local' / 'share' / 'timelawg' / 'screenshots' / 'actions'

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Action Screenshot module test")
    print(f"Windows APIs available: {WINDOWS_APIS_AVAILABLE}")
    print(f"pynput available: {PYNPUT_AVAILABLE}")
    print(f"Default action screenshot directory: {get_action_screenshot_directory()}")

    if WINDOWS_APIS_AVAILABLE and PYNPUT_AVAILABLE:
        print("\nStarting action screenshot capture test...")
        print("Click your mouse, press Enter, or drag to test screenshot capture")
        print("Press Ctrl+C to stop\n")

        # Create test worker
        def mock_db_insert(**kwargs):
            print(f"DB Insert: captured_at={kwargs.get('captured_at', 'N/A')[:19]}, "
                  f"action={Path(kwargs.get('file_path', '')).stem.split('_')[-1]}")

        worker = ActionScreenshotWorker(
            screenshot_dir=get_action_screenshot_directory() / 'test',
            db_insert_callback=mock_db_insert,
            enabled=True
        )

        # Start listening
        worker.start()

        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping test...")
            worker.shutdown(wait=True)
            print(f"\n✓ Test complete")
            print(f"Stats: {worker.get_stats()}")
    else:
        print("\n⚠ Cannot test: Windows APIs or pynput not available")
