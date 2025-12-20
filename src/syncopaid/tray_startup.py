"""
Windows startup registry management for SyncoPaid.

Provides functions to:
- Check if application is set to start with Windows
- Enable/disable startup via Windows registry
- Migrate old registry entries
- Sync registry to match user preferences
"""

import logging
import sys
from pathlib import Path

# Platform detection
WINDOWS = sys.platform == 'win32'

# Windows registry for startup management
if WINDOWS:
    import winreg


def is_startup_enabled() -> bool:
    """
    Check if the application is set to start with Windows.

    Returns:
        True if startup is enabled, False otherwise.
    """
    if not WINDOWS:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, "SyncoPaid")
            winreg.CloseKey(key)
            return bool(value)
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        logging.error(f"Error checking startup status: {e}")
        return False


def _get_canonical_exe_path() -> str:
    """
    Get the canonical executable path for registry startup.

    If running as an old executable name (e.g., SyncoPaid.exe) but
    SyncoPaid.exe exists in the same directory, returns the path
    to SyncoPaid.exe instead. This enables seamless migration when
    both files are deployed to a shared location.

    Returns:
        Path to SyncoPaid.exe if available, otherwise current executable.
    """
    current_exe = Path(sys.executable)
    current_name = current_exe.name.lower()

    # If already running as SyncoPaid.exe, use current path
    if current_name == 'syncopaid.exe':
        return str(current_exe)

    # Check if SyncoPaid.exe exists in the same directory
    syncopaid_exe = current_exe.parent / 'SyncoPaid.exe'
    if syncopaid_exe.exists():
        logging.info(f"Migration: using {syncopaid_exe} instead of {current_exe}")
        return str(syncopaid_exe)

    # Fall back to current executable
    return str(current_exe)


def enable_startup() -> bool:
    """
    Enable the application to start with Windows.

    Adds a registry entry pointing to SyncoPaid.exe. If running as an
    old executable (e.g., SyncoPaid.exe), will point to SyncoPaid.exe
    in the same directory if it exists.

    Returns:
        True if successful, False otherwise.
    """
    if not WINDOWS:
        logging.warning("Startup management only available on Windows")
        return False

    try:
        # Get the current executable path
        exe_path = sys.executable

        # Only enable startup for compiled executables, not python.exe
        if exe_path.lower().endswith(('python.exe', 'pythonw.exe')):
            logging.info("Running in development mode - startup not enabled")
            return False

        # Get canonical path (migrates to SyncoPaid.exe if available)
        exe_path = _get_canonical_exe_path()

        # Open/create the registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # Set the value
        winreg.SetValueEx(key, "SyncoPaid", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

        logging.info(f"Startup enabled: {exe_path}")
        return True

    except Exception as e:
        logging.error(f"Error enabling startup: {e}")
        return False


def disable_startup() -> bool:
    """
    Disable the application from starting with Windows.

    Removes the registry entry.

    Returns:
        True if successful, False otherwise.
    """
    if not WINDOWS:
        logging.warning("Startup management only available on Windows")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        try:
            winreg.DeleteValue(key, "SyncoPaid")
            winreg.CloseKey(key)
            logging.info("Startup disabled")
            return True
        except FileNotFoundError:
            # Value doesn't exist - that's fine
            winreg.CloseKey(key)
            return True

    except Exception as e:
        logging.error(f"Error disabling startup: {e}")
        return False


def _migrate_old_startup_entry() -> bool:
    """
    Migrate old SyncoPaid registry entry to SyncoPaid.

    Removes the old "SyncoPaid" entry if it exists.

    Returns:
        True if migration was performed, False otherwise.
    """
    if not WINDOWS:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ
        )

        try:
            # Check if old entry exists
            winreg.QueryValueEx(key, "SyncoPaid")
            # If we get here, old entry exists - delete it
            winreg.DeleteValue(key, "SyncoPaid")
            winreg.CloseKey(key)
            logging.info("Migrated: removed old SyncoPaid registry entry")
            return True
        except FileNotFoundError:
            # Old entry doesn't exist - nothing to migrate
            winreg.CloseKey(key)
            return False

    except Exception as e:
        logging.error(f"Error migrating old startup entry: {e}")
        return False


def sync_startup_registry(start_on_boot: bool) -> bool:
    """
    Sync the Windows startup registry entry to match the config setting.

    This should be called on every app startup to ensure:
    1. Old SyncoPaid entries are migrated
    2. Registry matches the user's saved preference
    3. Executable path is current (handles moves/renames)

    Args:
        start_on_boot: The user's preference from config

    Returns:
        True if registry now matches the desired state, False on error.
    """
    if not WINDOWS:
        return False

    # First, migrate any old SyncoPaid entry
    _migrate_old_startup_entry()

    # Now sync registry to match config
    if start_on_boot:
        return enable_startup()
    else:
        return disable_startup()
