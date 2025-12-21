"""
Utility functions for SyncoPaid UI windows.

Contains helper functions for duration parsing and window icon management.
"""

import sys
import logging
import tkinter as tk
from pathlib import Path

from syncopaid.tray import get_resource_path


def parse_duration_to_seconds(duration_str: str) -> float:
    """
    Parse a duration string like '2h 15m' or '45m' or '30s' back to seconds.

    Args:
        duration_str: Duration in format from format_duration()

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0

    total = 0.0

    # Handle hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        total += int(parts[0].strip()) * 3600
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle minutes
    if 'm' in duration_str:
        parts = duration_str.split('m')
        total += int(parts[0].strip()) * 60
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle seconds
    if 's' in duration_str:
        parts = duration_str.split('s')
        total += int(parts[0].strip())

    return total


def set_window_icon(root: tk.Tk) -> None:
    """Set the SyncoPaid icon on a tkinter window (Main window)."""
    try:
        if sys.platform == 'win32':
            icon_path = get_resource_path("assets/SYNCOPaiD.ico")
            logging.debug(f"Window icon path: {icon_path}")
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
                logging.debug("Window icon set successfully")
            else:
                logging.warning(f"Window icon not found: {icon_path}")
    except Exception as e:
        logging.warning(f"Could not set window icon: {e}")
