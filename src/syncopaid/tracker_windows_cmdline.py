"""
Command line tracking functionality for Windows.

Provides functions to get and redact process command line arguments.
"""

import sys
import logging
from typing import Optional
import re

# Platform detection
WINDOWS = sys.platform == 'win32'

if WINDOWS:
    try:
        import psutil
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
else:
    WINDOWS_APIS_AVAILABLE = False


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
