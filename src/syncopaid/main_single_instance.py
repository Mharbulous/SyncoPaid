"""
Single-instance enforcement for SyncoPaid.

Uses Windows mutex to ensure only one instance of the application runs at a time.
"""

import ctypes
import sys

# Single-instance enforcement using Windows mutex
_MUTEX_NAME = "SyncoPaidTracker_SingleInstance_Mutex"
_mutex_handle = None


def acquire_single_instance():
    """
    Acquire a Windows mutex to ensure only one instance runs.

    Returns:
        True if this is the only instance, False if another instance is running.
    """
    global _mutex_handle

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183

    # Create named mutex
    _mutex_handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

    # Check if mutex already existed
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        if _mutex_handle:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
        return False

    return True


def release_single_instance():
    """Release the Windows mutex."""
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None
