"""
Screenshot timing and submission logic for TrackerLoop.

Manages periodic screenshot capture based on configured intervals.
"""

import time
import logging
from typing import Dict, Optional

from syncopaid.tracker_screenshot import submit_screenshot
from syncopaid.tracker_windows import WINDOWS_APIS_AVAILABLE


class ScreenshotScheduler:
    """
    Manages screenshot capture timing and submission.

    Ensures screenshots are captured at regular intervals and submitted
    to the screenshot worker for processing.
    """

    def __init__(self, screenshot_worker, screenshot_interval: float = 10.0):
        """
        Initialize screenshot scheduler.

        Args:
            screenshot_worker: The worker that processes screenshot submissions
            screenshot_interval: Seconds between screenshot attempts
        """
        self.screenshot_worker = screenshot_worker
        self.screenshot_interval = screenshot_interval
        self.last_screenshot_time: float = 0
        self._diagnostic_logged: bool = False

    def maybe_capture_screenshot(self, window: Dict, idle_seconds: float) -> None:
        """
        Check if a screenshot should be captured and submit if needed.

        Args:
            window: Current window information dictionary
            idle_seconds: How many seconds the user has been idle
        """
        if not self.screenshot_worker:
            return

        current_time = time.time()
        time_since_last = current_time - self.last_screenshot_time

        # Log diagnostic info on first screenshot attempt
        if not self._diagnostic_logged:
            logging.info(
                f"Screenshot capture enabled: interval={self.screenshot_interval}s, "
                f"tracker_apis_available={WINDOWS_APIS_AVAILABLE}"
            )
            self._diagnostic_logged = True

        if time_since_last >= self.screenshot_interval:
            logging.debug(f"Triggering screenshot capture (elapsed: {time_since_last:.1f}s)")
            submit_screenshot(self.screenshot_worker, window, idle_seconds)
            self.last_screenshot_time = current_time
