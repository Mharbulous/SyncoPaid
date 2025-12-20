"""
Screenshot capture utilities for action-based screenshots.

Handles window capture, image resizing, and file path generation.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL regardless of platform
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    PIL_AVAILABLE = False
    logging.warning(f"PIL import failed: {e}")
    class Image:
        class Image:
            pass

if WINDOWS:
    try:
        import win32gui
        import mss
        WINDOWS_APIS_AVAILABLE = PIL_AVAILABLE and True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Screenshot APIs not available. Install pywin32, Pillow, and mss.")
else:
    WINDOWS_APIS_AVAILABLE = False


# Apps to skip screenshot capture
SKIP_APPS = {
    'LockApp.exe',
    'ScreenSaver.scr',
    'LogonUI.exe'
}


def capture_window(hwnd: int) -> Optional[Image.Image]:
    """
    Capture screenshot of the specified window.

    Args:
        hwnd: Windows window handle

    Returns:
        PIL Image or None if capture failed
    """
    if not WINDOWS_APIS_AVAILABLE:
        return None

    try:
        # Validate window
        if not win32gui.IsWindow(hwnd):
            return None

        if not win32gui.IsWindowVisible(hwnd):
            return None

        if win32gui.IsIconic(hwnd):
            return None

        # Get window rectangle
        rect = win32gui.GetWindowRect(hwnd)
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1

        # Validate dimensions
        if width <= 0 or height <= 0:
            return None

        if width > 10000 or height > 10000:
            return None

        # Check if completely off-screen
        if x2 < 0 or y2 < 0:
            return None

        # Capture screenshot using MSS library (fixes secondary monitor black screenshots)
        # MSS handles multi-monitor coordinate systems correctly, unlike PIL's ImageGrab
        # which has known bugs with secondary monitors (Pillow #1547, #7898)
        with mss.mss() as sct:
            # Define the capture region using MSS's monitor dict format
            monitor = {
                "left": x1,
                "top": y1,
                "width": width,
                "height": height
            }

            # Capture the screenshot
            screenshot = sct.grab(monitor)

            # Convert MSS screenshot to PIL Image
            # MSS returns BGRA format, convert to RGB for PIL
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        return img

    except Exception as e:
        logging.error(f"Error capturing window: {e}")
        return None


def resize_if_needed(img: Image.Image, max_dimension: int) -> Image.Image:
    """
    Resize image if either dimension exceeds max_dimension.

    Args:
        img: PIL Image
        max_dimension: Maximum width or height in pixels

    Returns:
        Resized PIL Image (or original if no resize needed)
    """
    width, height = img.size
    max_dim = max(width, height)

    if max_dim <= max_dimension:
        return img

    # Calculate new dimensions maintaining aspect ratio
    scale = max_dimension / max_dim
    new_width = int(width * scale)
    new_height = int(height * scale)

    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def get_screenshot_path(screenshot_dir: Path, timestamp: str, action: str) -> Path:
    """
    Generate file path for action screenshot.

    Format: {screenshot_dir}/YYYY-MM-DD/YYYY-MM-DD_HH-mm-ss_UTC_{action}.jpg
    Examples:
        - 2025-12-10/2025-12-10_00-33-30_UTC-08-00_click.jpg
        - 2025-12-10/2025-12-10_14-22-15_UTC-08-00_enter.jpg
        - 2025-12-10/2025-12-10_14-22-15_UTC-08-00_focus.jpg

    Args:
        screenshot_dir: Base directory for screenshots
        timestamp: ISO timestamp with timezone information
        action: Action type ('click', 'enter', 'drag', 'drop', 'focus')

    Returns:
        Path object for screenshot file
    """
    dt = datetime.fromisoformat(timestamp)

    # Create date-based subdirectory (local date)
    date_dir = screenshot_dir / dt.strftime('%Y-%m-%d')
    date_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with date, time, and timezone
    date_str = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H-%M-%S')
    tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", "EST", or "UTC-08:00", etc.

    # Sanitize timezone for Windows filenames (remove colons)
    # "UTC-08:00" -> "UTC-08-00", "PST" -> "PST"
    tz_abbr = tz_abbr.replace(':', '-')

    filename = f"{date_str}_{time_str}_{tz_abbr}_{action}.jpg"
    return date_dir / filename


def get_action_screenshot_directory() -> Path:
    """
    Get the default action screenshot storage directory.

    Returns:
        Path to action screenshot directory
    """
    import sys
    import os

    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        screenshot_dir = appdata / 'SyncoPaid' / 'screenshots' / 'actions'
    else:
        screenshot_dir = Path.home() / '.local' / 'share' / 'SyncoPaid' / 'screenshots' / 'actions'

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir
