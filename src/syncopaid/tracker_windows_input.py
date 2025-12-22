"""
Input activity detection functionality for Windows.

Provides functions to detect keyboard and mouse activity without capturing content.
Privacy-focused: only detects activity, never captures keystrokes or content.
"""

import sys

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
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
else:
    WINDOWS_APIS_AVAILABLE = False


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
