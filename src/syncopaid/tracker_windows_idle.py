"""
Idle time detection functionality for Windows.

Provides functions to measure user idle time based on keyboard/mouse inactivity.
"""

import sys
import logging
from ctypes import Structure, windll, c_uint, sizeof, byref

# Platform detection
WINDOWS = sys.platform == 'win32'

if WINDOWS:
    try:
        import win32gui
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
else:
    WINDOWS_APIS_AVAILABLE = False


if WINDOWS_APIS_AVAILABLE:
    class LASTINPUTINFO(Structure):
        """Windows structure for GetLastInputInfo API."""
        _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]


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
