"""
Window capture and image processing utilities.

Provides low-level screenshot capture using Windows APIs (win32gui, mss)
and image processing operations (resize, pixel comparison).
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL regardless of platform (needed for type hints)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    PIL_AVAILABLE = False
    logging.warning(f"PIL import failed: {e}. Screenshots will be disabled.")
    # Create dummy type for non-PIL environments
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
        logging.warning("Screenshot APIs not available. Install pywin32, Pillow, imagehash, and mss.")
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
        # Mock screenshot for testing on non-Windows
        logging.debug("Mock screenshot (non-Windows platform)")
        return None

    try:
        # Validate window
        if not win32gui.IsWindow(hwnd):
            logging.debug("Invalid window handle")
            return None

        if not win32gui.IsWindowVisible(hwnd):
            logging.debug("Window not visible")
            return None

        if win32gui.IsIconic(hwnd):
            logging.debug("Window is minimized")
            return None

        # Get window rectangle
        rect = win32gui.GetWindowRect(hwnd)
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1

        # Validate dimensions
        if width <= 0 or height <= 0:
            logging.debug(f"Invalid window dimensions: {width}x{height}")
            return None

        if width > 10000 or height > 10000:
            logging.warning(f"Window too large: {width}x{height}")
            return None

        # Check if completely off-screen
        if x2 < 0 or y2 < 0:
            logging.debug("Window completely off-screen")
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
        max_dimension: Maximum allowed width or height

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


def quick_pixel_check(img: Image.Image, previous_path: str, tolerance: int = 10) -> bool:
    """
    Fast-path optimization: sample 5 pixels (corners + center).

    If all pixels are within tolerance, skip expensive hash computation.

    Args:
        img: Current image
        previous_path: Path to previous screenshot
        tolerance: RGB difference tolerance (default: 10)

    Returns:
        True if images appear identical via pixel sampling
    """
    try:
        import os
        if not os.path.exists(previous_path):
            return False

        prev_img = Image.open(previous_path)

        # Must be same size
        if img.size != prev_img.size:
            return False

        width, height = img.size

        # Sample 5 points: 4 corners + center
        sample_points = [
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),
            (width // 2, height // 2)
        ]

        for x, y in sample_points:
            pixel1 = img.getpixel((x, y))
            pixel2 = prev_img.getpixel((x, y))

            # Convert to tuples if needed
            if isinstance(pixel1, int):
                pixel1 = (pixel1, pixel1, pixel1)
            if isinstance(pixel2, int):
                pixel2 = (pixel2, pixel2, pixel2)

            # Check RGB differences
            for i in range(min(3, len(pixel1))):
                if abs(pixel1[i] - pixel2[i]) > tolerance:
                    return False

        # All sampled pixels are within tolerance
        return True

    except Exception as e:
        logging.debug(f"Quick pixel check failed: {e}")
        return False
