"""
Lock screen and screensaver detection functionality for Windows.

Provides functions to detect when the workstation is locked or screensaver is active.
"""

import sys
import logging

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import Windows-specific ctypes only on Windows
if WINDOWS:
    from ctypes import windll
else:
    windll = None

if WINDOWS:
    try:
        import win32gui
        import win32process
        import win32con
        import psutil
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
else:
    WINDOWS_APIS_AVAILABLE = False


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
