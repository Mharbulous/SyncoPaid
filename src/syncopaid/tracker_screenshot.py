"""
Screenshot submission utilities for TrackerLoop.

Handles the integration between window tracking and screenshot capture,
submitting screenshot requests to the ScreenshotWorker at regular intervals.
"""

import logging
from datetime import datetime
from typing import Dict

from syncopaid.tracker_windows import WINDOWS_APIS_AVAILABLE

if WINDOWS_APIS_AVAILABLE:
    import win32gui


def submit_screenshot(screenshot_worker, window: Dict, idle_seconds: float):
    """
    Submit a screenshot capture request to the worker.

    Args:
        screenshot_worker: ScreenshotWorker instance to submit to
        window: Window information dict from get_active_window()
        idle_seconds: Current idle time

    Note:
        This function will log a warning once per session if Windows APIs
        are not available, but will otherwise silently skip screenshot capture.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Log this once per session to inform user why screenshots aren't working
        if not hasattr(submit_screenshot, '_platform_warning_logged'):
            logging.warning(
                "Cannot capture screenshots: Windows APIs not available. "
                "This is expected on non-Windows platforms or if pywin32/psutil are not installed."
            )
            submit_screenshot._platform_warning_logged = True
        return

    try:
        # Get window handle
        hwnd = win32gui.GetForegroundWindow()
        timestamp = datetime.now().astimezone().isoformat()

        # Submit to worker (non-blocking)
        logging.debug(f"Submitting screenshot for {window['app']}")
        screenshot_worker.submit(
            hwnd=hwnd,
            timestamp=timestamp,
            window_app=window['app'],
            window_title=window['title'],
            idle_seconds=idle_seconds
        )

    except Exception as e:
        logging.error(f"Error submitting screenshot: {e}", exc_info=True)
