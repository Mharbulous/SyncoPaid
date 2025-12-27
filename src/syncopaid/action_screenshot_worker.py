"""
Action screenshot worker class.

Handles the coordination of action-based screenshot capture, including:
- Event handler management
- Thread pool for async capture
- Screenshot capture and save operations
- Statistics tracking
"""

import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from syncopaid.action_screenshot_events import ActionEventHandler, PYNPUT_AVAILABLE
from syncopaid.action_screenshot_capture import (
    capture_window,
    resize_if_needed,
    get_screenshot_path,
    WINDOWS_APIS_AVAILABLE,
    SKIP_APPS
)

try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    pass

from datetime import datetime


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
        self.enabled = enabled

        # Thread pool for async capture
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='action_screenshot')

        # Event handler
        self.event_handler = ActionEventHandler(
            capture_callback=self._capture_action_screenshot,
            throttle_seconds=throttle_seconds
        )

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

        self.event_handler.start()
        logging.info(f"Action screenshot listeners started. Screenshot dir: {self.screenshot_dir}")

    def stop(self):
        """Stop listening for user actions."""
        self.event_handler.stop()
        logging.info("Action screenshot listeners stopped")

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
            img = capture_window(hwnd)
            if img is None:
                logging.warning(f"Screenshot capture failed for {action} action (hwnd={hwnd})")
                return

            logging.info(f"Action screenshot: captured image {img.size[0]}x{img.size[1]} for {action}")

            # Resize if needed
            img = resize_if_needed(img, self.max_dimension)

            # Generate timestamp (use local timezone, consistent with periodic screenshots)
            timestamp = datetime.now().astimezone().isoformat()

            # Generate file path
            file_path = get_screenshot_path(self.screenshot_dir, timestamp, action)

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

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the action screenshot worker.

        Args:
            wait: Whether to wait for pending tasks
            timeout: Max seconds to wait
        """
        # Stop listeners first
        self.stop()

        # Get stats from event handler
        stats = self.event_handler.get_stats()
        logging.info(
            f"ActionScreenshotWorker shutting down. "
            f"Stats: clicks={stats['click_captures']}, "
            f"enters={stats['enter_captures']}, "
            f"drag_starts={stats['drag_start_captures']}, "
            f"drag_ends={stats['drag_end_captures']}, "
            f"focus={stats['focus_captures']}, "
            f"throttled={stats['throttled']}"
        )

        # Shutdown thread pool
        self.executor.shutdown(wait=wait, cancel_futures=not wait)

    def get_stats(self) -> dict:
        """Get action screenshot capture statistics."""
        return self.event_handler.get_stats()
