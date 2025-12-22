"""
Active window detection functionality for Windows.

Provides functions to get information about the currently active foreground window,
including app name, title, PID, and contextual information (URLs, file paths).
"""

import sys
import logging
from typing import Dict, Optional

from syncopaid.context_extraction import extract_context

# Platform detection
WINDOWS = sys.platform == 'win32'

if WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Windows APIs not available. Install pywin32 and psutil.")
else:
    WINDOWS_APIS_AVAILABLE = False


def get_active_window(config=None) -> Dict[str, Optional[str]]:
    """
    Get information about the currently active foreground window.
    Now includes redacted cmdline for instance differentiation.

    Args:
        config: Optional Config object to control URL extraction behavior

    Returns:
        Dictionary with keys:
        - 'app': Executable name (e.g., 'WINWORD.EXE', 'chrome.exe')
        - 'title': Window title text
        - 'pid': Process ID (for debugging)
        - 'url': Extracted contextual information (URL, subject, or filepath)
        - 'cmdline': Redacted command line arguments (list of strings)

    Note: Returns mock data on non-Windows platforms for testing.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock data for testing on non-Windows platforms
        import random
        mock_apps = [
            ("WINWORD.EXE", "Smith-Contract-v2.docx - Word", ["WINWORD.EXE", "[PATH]\\Smith-Contract-v2.docx"]),
            ("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome", ["chrome.exe", "--profile-directory=Default"]),
            ("OUTLOOK.EXE", "Inbox - user@lawfirm.com - Outlook", ["OUTLOOK.EXE"]),
        ]
        app, title, cmdline = random.choice(mock_apps)
        url_extraction_enabled = config.url_extraction_enabled if config else True
        url = extract_context(app, title) if url_extraction_enabled else None
        return {"app": app, "title": title, "pid": 0, "url": url, "cmdline": cmdline}

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Handle signed/unsigned integer overflow from Windows API
        # Windows returns unsigned 32-bit PID, but Python may interpret as signed
        if pid < 0:
            pid = pid & 0xFFFFFFFF  # Convert to unsigned

        process_name = None
        cmdline = None

        try:
            process = psutil.Process(pid)
            process_name = process.name()
            raw_cmdline = process.cmdline()
            if raw_cmdline:
                from .tracker_windows_cmdline import redact_sensitive_paths
                cmdline = redact_sensitive_paths(raw_cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            pass

        # Extract URL if browser and config enabled
        url = None
        url_extraction_enabled = config.url_extraction_enabled if config else True

        if url_extraction_enabled:
            # Import here to avoid circular dependency
            from .url_extractor import extract_browser_url
            url = extract_browser_url(process_name, timeout_ms=100)

            # Fallback to title-based extraction if UI Automation fails
            if not url:
                url = extract_context(process_name, title)

        if url:
            logging.debug(f"Extracted context from {process_name}: {url[:50]}...")  # Log first 50 chars
        elif process_name and title:
            # Only log if we had a valid app and title but extraction returned None
            logging.debug(f"No context extracted from {process_name}: {title[:50]}...")

        return {"app": process_name, "title": title, "pid": pid, "url": url, "cmdline": cmdline}

    except Exception as e:
        logging.error(f"Error getting active window: {e}")
        return {"app": None, "title": None, "pid": None, "url": None, "cmdline": None}
