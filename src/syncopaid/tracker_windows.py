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
    Now includes redacted cmdline for instance differentiation.

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
        url = extract_context(app, title)
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
                cmdline = redact_sensitive_paths(raw_cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            pass

        # Extract contextual information
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


def is_key_pressed(vk_code: int) -> bool:
    """
    Check if a specific virtual key is currently pressed.

    Uses GetAsyncKeyState to check key state without blocking.
    Privacy note: Only checks if key is pressed, never captures which key.

    Args:
        vk_code: Windows virtual key code

    Returns:
        True if key is currently pressed, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    try:
        # High-order bit indicates key is currently pressed
        return bool(windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
    except Exception:
        return False


def get_keyboard_activity() -> bool:
    """
    Check if any keyboard key is currently being pressed.

    Checks a range of common keys to detect typing activity.
    Privacy note: Only detects activity, never captures content.

    Returns:
        True if any typing activity detected, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    # Check alphanumeric keys (0x30-0x5A covers 0-9, A-Z)
    for vk in range(0x30, 0x5B):
        if is_key_pressed(vk):
            return True

    # Check common punctuation/editing keys
    editing_keys = [
        0x08,  # Backspace
        0x09,  # Tab
        0x0D,  # Enter
        0x20,  # Space
        0xBA,  # Semicolon
        0xBB,  # Equals
        0xBC,  # Comma
        0xBD,  # Minus
        0xBE,  # Period
        0xBF,  # Slash
    ]
    for vk in editing_keys:
        if is_key_pressed(vk):
            return True

    return False


def get_mouse_activity() -> bool:
    """
    Check if any mouse button is currently being pressed.

    Checks left, right, and middle mouse buttons.

    Returns:
        True if any mouse button is pressed, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    # Virtual key codes for mouse buttons
    mouse_buttons = [
        0x01,  # VK_LBUTTON (left)
        0x02,  # VK_RBUTTON (right)
        0x04,  # VK_MBUTTON (middle)
    ]

    for vk in mouse_buttons:
        if is_key_pressed(vk):
            return True

    return False


# ============================================================================
# COMMAND LINE TRACKING
# ============================================================================

def get_process_cmdline(pid: int) -> Optional[list]:
    """
    Get command line arguments for a process by PID.
    Returns None if unavailable (AccessDenied, NoSuchProcess, etc.)
    """
    if not WINDOWS_APIS_AVAILABLE:
        return None

    try:
        process = psutil.Process(pid)
        cmdline = process.cmdline()
        return cmdline if cmdline else None
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
        return None
    except Exception as e:
        logging.debug(f"Error getting cmdline for PID {pid}: {e}")
        return None


def redact_sensitive_paths(cmdline: list) -> list:
    """
    Redact sensitive file paths from command line arguments.
    Preserves profile flags, redacts user paths.
    """
    if not cmdline:
        return []

    import re

    result = []
    path_pattern = re.compile(r'^[A-Za-z]:\\')
    user_pattern = re.compile(r'\\Users\\[^\\]+\\', re.IGNORECASE)

    for arg in cmdline:
        if not arg:
            continue

        # Preserve profile directory flags
        if arg.startswith('--profile-directory=') or arg.startswith('--profile='):
            result.append(arg)
            continue

        # Redact file paths
        if path_pattern.match(arg):
            # Extract filename using backslash split (works cross-platform)
            parts = arg.split('\\')
            filename = parts[-1] if parts else arg
            if user_pattern.search(arg):
                result.append(f"[REDACTED_PATH]\\{filename}")
            else:
                result.append(f"[PATH]\\{filename}")
            continue

        result.append(arg)

    return result


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
