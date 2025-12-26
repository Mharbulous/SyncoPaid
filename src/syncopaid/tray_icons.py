"""
Icon creation and rendering for SyncoPaid system tray.

Provides functions to:
- Locate resource files (works in dev and PyInstaller)
- Create state-specific tray icons (active, paused, inactive)
- Add overlay graphics (sleep emoji, pause symbol)
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None
    logging.warning("PIL not available. Install with: pip install Pillow")


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    In development: uses __file__ to locate resources relative to source
    In PyInstaller exe: uses sys._MEIPASS to locate bundled resources

    Args:
        relative_path: Path relative to syncopaid package (e.g., "assets/icon.ico")

    Returns:
        Absolute Path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        return base_path / "syncopaid" / relative_path
    else:
        # Running in development
        return Path(__file__).parent / relative_path


def create_icon_image(state: str = "on") -> Optional["Image.Image"]:
    """
    Create system tray icon using state-specific icon files.

    Args:
        state: One of "on" (tracking), "paused" (user paused), "inactive" (no activity)

    Returns:
        PIL Image object for the icon, or None if PIL not available
    """
    if not TRAY_AVAILABLE:
        return None

    size = 64

    # Select icon file based on state
    # Active (on): green stopwatch
    # Paused: orange stopwatch (user clicked pause)
    # Inactive: faded stopwatch with sleep emoji overlay (5min idle)
    # Feedback: orange stopwatch (brief flash for user feedback)
    # Quitting: faded stopwatch (no overlay, immediate quit feedback)
    if state == "inactive":
        ico_path = get_resource_path("assets/stopwatch-pictogram-faded.ico")
    elif state == "paused":
        ico_path = get_resource_path("assets/stopwatch-paused.ico")
    elif state == "feedback":
        ico_path = get_resource_path("assets/stopwatch-pictogram-orange2.ico")
    elif state == "quitting":
        ico_path = get_resource_path("assets/stopwatch-pictogram-faded.ico")
    else:  # "on" or default
        ico_path = get_resource_path("assets/stopwatch-pictogram-green.ico")

    image = None
    if ico_path.exists():
        try:
            # Open ICO and get the best size for system tray
            ico = Image.open(ico_path)
            # ICO files contain multiple sizes; resize to target
            image = ico.convert('RGBA')
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            # Clear ICO metadata so pystray serializes a clean icon
            # (prevents Windows LoadImage issues with stale size info)
            image.info.clear()
        except Exception as e:
            logging.warning(f"Could not load ICO icon: {e}")

    if image is None:
        # Fallback to blank canvas if no icon found
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Add overlays based on state
    if state == "inactive":
        image = add_sleep_overlay(image)
    elif state == "paused":
        image = add_pause_overlay(image)

    return image


def add_sleep_overlay(image: "Image.Image") -> "Image.Image":
    """
    Add a 💤 overlay to the icon for inactive state.

    Args:
        image: Base icon image

    Returns:
        Image with sleep overlay composited
    """
    if not TRAY_AVAILABLE:
        return image

    size = image.size[0]
    overlay_size = size // 2  # Sleep emoji takes up half the icon

    # Create overlay with sleep emoji
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to use Windows emoji font, fall back to text "zzz"
    emoji_text = "💤"
    fallback_text = "zzz"

    try:
        # Windows has Segoe UI Emoji font
        font = ImageFont.truetype("seguiemj.ttf", overlay_size)
        text = emoji_text
    except Exception:
        try:
            # Fallback to any available font
            font = ImageFont.truetype("arial.ttf", overlay_size // 2)
            text = fallback_text
        except Exception:
            # Last resort: default font
            font = ImageFont.load_default()
            text = fallback_text

    # Position in bottom-right corner
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = size - text_width - 2
    y = size - text_height - 2

    # Draw with slight shadow for visibility
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Composite overlay onto base image
    return Image.alpha_composite(image, overlay)


def add_pause_overlay(image: "Image.Image") -> "Image.Image":
    """
    Add a ❚❚ overlay to the icon for paused state.

    Args:
        image: Base icon image

    Returns:
        Image with pause overlay composited
    """
    if not TRAY_AVAILABLE:
        return image

    size = image.size[0]
    overlay_size = size // 2

    # Create overlay with pause symbol
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    text = "❚❚"

    try:
        # Use a font that renders the pause bars well
        font = ImageFont.truetype("arial.ttf", overlay_size)
    except Exception:
        font = ImageFont.load_default()

    # Position in bottom-right corner
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = size - text_width - 2
    y = size - text_height - 2

    # Draw with shadow for visibility
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Composite overlay onto base image
    return Image.alpha_composite(image, overlay)
