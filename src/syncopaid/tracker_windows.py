"""
Windows API functions for active window detection and idle time tracking.

This module provides platform-specific functionality for:
- Getting active window information (app name, title, PID)
- Measuring user idle time (keyboard/mouse inactivity)
- Mock data for non-Windows platforms
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
        from ctypes import Structure, windll, c_uint, sizeof, byref
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Windows APIs not available. Install pywin32 and psutil.")
else:
    WINDOWS_APIS_AVAILABLE = False


# ============================================================================
# WINDOWS API STRUCTURES
# ============================================================================

if WINDOWS_APIS_AVAILABLE:
    class LASTINPUTINFO(Structure):
        """Windows structure for GetLastInputInfo API."""
        _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]


# ============================================================================
# ACTIVE WINDOW DETECTION
# ============================================================================

def get_active_window() -> Dict[str, Optional[str]]:
    """
    Get information about the currently active foreground window.

    Returns:
        Dictionary with keys:
        - 'app': Executable name (e.g., 'WINWORD.EXE', 'chrome.exe')
        - 'title': Window title text
        - 'pid': Process ID (for debugging)
        - 'url': Extracted contextual information (URL, subject, or filepath)

    Note: Returns mock data on non-Windows platforms for testing.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock data for testing on non-Windows platforms
        import random
        mock_apps = [
            ("WINWORD.EXE", "Smith-Contract-v2.docx - Word"),
            ("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome"),
            ("OUTLOOK.EXE", "Inbox - user@lawfirm.com - Outlook"),
        ]
        app, title = random.choice(mock_apps)
        url = extract_context(app, title)
        return {"app": app, "title": title, "pid": 0, "url": url}

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Handle signed/unsigned integer overflow from Windows API
        # Windows returns unsigned 32-bit PID, but Python may interpret as signed
        if pid < 0:
            pid = pid & 0xFFFFFFFF  # Convert to unsigned

        try:
            process = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            process = None

        # Extract contextual information
        url = extract_context(process, title)
        if url:
            logging.debug(f"Extracted context from {process}: {url[:50]}...")  # Log first 50 chars
        elif process and title:
            # Only log if we had a valid app and title but extraction returned None
            logging.debug(f"No context extracted from {process}: {title[:50]}...")

        return {"app": process, "title": title, "pid": pid, "url": url}

    except Exception as e:
        logging.error(f"Error getting active window: {e}")
        return {"app": None, "title": None, "pid": None, "url": None}


# ============================================================================
# IDLE TIME DETECTION
# ============================================================================

def get_idle_seconds() -> float:
    """
    Get the number of seconds since the last keyboard or mouse input.

    Uses Windows GetLastInputInfo API to detect user inactivity.

    Returns:
        Float representing idle seconds. Returns 0.0 on non-Windows platforms.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock: alternate between active (0s) and occasionally idle
        import random
        return random.choice([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 200.0])

    try:
        info = LASTINPUTINFO()
        info.cbSize = sizeof(info)
        windll.user32.GetLastInputInfo(byref(info))
        millis = windll.kernel32.GetTickCount() - info.dwTime
        return millis / 1000.0

    except Exception as e:
        logging.error(f"Error getting idle time: {e}")
        return 0.0


# ============================================================================
# LOCK SCREEN AND SCREENSAVER DETECTION
# ============================================================================

def is_screensaver_active() -> bool:
    """
    Check if Windows screensaver is currently active.

    Screensavers run as .scr processes and become the foreground window.
    Detection strategy: check if foreground window process ends with .scr

    Returns:
        True if screensaver is active, False otherwise (including on non-Windows)
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    try:
        # Get foreground window
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False

        # Get process ID from window handle
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return False

        # Get process name
        process = psutil.Process(pid)
        exe_name = process.name().lower()

        # Screensavers have .scr extension
        return exe_name.endswith('.scr')

    except Exception as e:
        logging.debug(f"Error checking screensaver: {e}")
        return False


def is_workstation_locked() -> bool:
    """
    Check if Windows workstation is locked (Ctrl+Alt+Del, Win+L, or screen lock).

    Uses OpenInputDesktop API which returns NULL when locked.
    More reliable than session switch events for polling-based detection.

    Returns:
        True if workstation is locked, False otherwise (including on non-Windows)
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    try:
        # Import win32con for constants
        import win32con

        # OpenInputDesktop returns NULL (0) when desktop is locked
        # Using ctypes windll which is already imported
        hdesk = windll.user32.OpenInputDesktop(0, False, win32con.MAXIMUM_ALLOWED)

        if hdesk == 0:
            return True  # Desktop is locked

        # Close the desktop handle
        windll.user32.CloseDesktop(hdesk)
        return False  # Desktop is not locked

    except Exception as e:
        logging.debug(f"Error checking workstation lock: {e}")
        return False
