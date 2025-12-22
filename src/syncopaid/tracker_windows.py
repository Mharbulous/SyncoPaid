"""
Windows API functions for active window detection and idle time tracking.

This module provides platform-specific functionality for:
- Getting active window information (app name, title, PID)
- Measuring user idle time (keyboard/mouse inactivity)
- Mock data for non-Windows platforms

This is the main entry point that re-exports all Windows tracking functionality
from specialized submodules.
"""

# Re-export all functions from submodules
from .tracker_windows_active import get_active_window
from .tracker_windows_idle import get_idle_seconds
from .tracker_windows_input import (
    is_key_pressed,
    get_keyboard_activity,
    get_mouse_activity,
)
from .tracker_windows_cmdline import (
    get_process_cmdline,
    redact_sensitive_paths,
)
from .tracker_windows_lock import (
    is_screensaver_active,
    is_workstation_locked,
)

__all__ = [
    'get_active_window',
    'get_idle_seconds',
    'is_key_pressed',
    'get_keyboard_activity',
    'get_mouse_activity',
    'get_process_cmdline',
    'redact_sensitive_paths',
    'is_screensaver_active',
    'is_workstation_locked',
]
