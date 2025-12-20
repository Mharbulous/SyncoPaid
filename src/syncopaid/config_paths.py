"""
Path resolution utilities for SyncoPaid configuration.

Handles platform-specific path detection for config files and database files.
Supports Windows (%LOCALAPPDATA%) and Unix-like systems (~/.config).
"""

import sys
import os
import logging
from pathlib import Path


def get_default_config_path() -> Path:
    """
    Get the default configuration file path for the current platform.

    Returns:
        Path object pointing to config.json location
    """
    if sys.platform == 'win32':
        # Windows: %LOCALAPPDATA%\SyncoPaid\config.json
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            # Fallback if LOCALAPPDATA not set
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        config_dir = appdata / 'SyncoPaid'
    else:
        # Linux/Mac: ~/.config/SyncoPaid/config.json
        config_dir = Path.home() / '.config' / 'SyncoPaid'

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'


def get_default_database_path() -> Path:
    """
    Get the default database file path for the current platform.

    Returns:
        Path object pointing to SyncoPaid.db location
    """
    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        db_dir = appdata / 'SyncoPaid'
    else:
        db_dir = Path.home() / '.local' / 'share' / 'SyncoPaid'

    db_dir.mkdir(parents=True, exist_ok=True)

    # Migration: rename old database if it exists
    old_db = db_dir / 'lawtime.db'
    new_db = db_dir / 'SyncoPaid.db'
    if old_db.exists() and not new_db.exists():
        logging.info(f"Migrating database from {old_db} to {new_db}")
        old_db.rename(new_db)

    return new_db
