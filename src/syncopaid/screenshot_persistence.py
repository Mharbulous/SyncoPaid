"""
Screenshot file path generation and persistence utilities.

Handles generating timestamped filenames with proper directory structure
and saving screenshots to disk.
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    import imagehash
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Create dummy types
    class Image:
        class Image:
            pass
    class imagehash:
        class ImageHash:
            pass


def get_screenshot_directory() -> Path:
    """
    Get the default screenshot storage directory.

    Returns:
        Path to screenshot directory
    """
    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        screenshot_dir = appdata / 'SyncoPaid' / 'screenshots' / 'periodic'
    else:
        screenshot_dir = Path.home() / '.local' / 'share' / 'SyncoPaid' / 'screenshots' / 'periodic'

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


def get_screenshot_path(screenshot_dir: Path, timestamp: str, window_app: Optional[str]) -> Path:
    """
    Generate file path for screenshot.

    Format: {screenshot_dir}/YYYY-MM-DD/YYYY-MM-DD_HH-MM-SS_TZ_appname.jpg
    Examples:
        - 2025-12-09/2025-12-09_23-25-05_PST_WindowsTerminal.jpg
        - 2025-12-10/2025-12-10_00-23-21_UTC-08-00_chrome.jpg

    Args:
        screenshot_dir: Base screenshot directory
        timestamp: ISO timestamp with timezone information
        window_app: Application name

    Returns:
        Path object for screenshot file
    """
    dt = datetime.fromisoformat(timestamp)

    # Create date-based subdirectory (local date)
    date_dir = screenshot_dir / dt.strftime('%Y-%m-%d')
    date_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date, time, and timezone abbreviation
    date_str = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H-%M-%S')
    tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", "EST", or "UTC-08:00", etc.

    # Sanitize timezone for Windows filenames (remove colons)
    # "UTC-08:00" -> "UTC-08-00", "PST" -> "PST"
    tz_abbr = tz_abbr.replace(':', '-')

    app_name = window_app if window_app else 'unknown'
    # Sanitize app name for filename
    app_name = app_name.replace('.exe', '').replace('.', '_')[:20]

    filename = f"{date_str}_{time_str}_{tz_abbr}_{app_name}.jpg"
    return date_dir / filename


def save_screenshot(
    img: Image.Image,
    file_path: Path,
    quality: int = 65
):
    """
    Save screenshot image as JPEG.

    Args:
        img: PIL Image to save
        file_path: Path where to save the image
        quality: JPEG quality 1-100 (default: 65)
    """
    img.save(str(file_path), 'JPEG', quality=quality, optimize=True)
    logging.info(f"Saved screenshot: {file_path}")
