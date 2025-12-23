"""
Color management and styling utilities for timeline view.

Provides consistent color mapping for applications and activity states.
"""

import hashlib
from typing import Optional, Dict


# Color palette for applications (bright, distinct colors)
APP_COLORS = [
    "#4285F4",  # Blue (Google blue)
    "#34A853",  # Green
    "#EA4335",  # Red
    "#FBBC05",  # Yellow
    "#9C27B0",  # Purple
    "#FF5722",  # Deep orange
    "#00BCD4",  # Cyan
    "#795548",  # Brown
    "#607D8B",  # Blue gray
    "#E91E63",  # Pink
]

IDLE_COLOR = "#D3D3D3"  # Light gray for idle periods

# Zoom level definitions (minutes visible)
ZOOM_LEVELS = {
    'day': 24 * 60,    # 1440 minutes
    'hour': 60,         # 60 minutes
    'minute': 15,       # 15 minutes
}

# Cache app -> color mapping for consistency
_app_color_cache: Dict[str, str] = {}


def get_app_color(app: Optional[str], is_idle: bool = False) -> str:
    """
    Get consistent color for an application.

    Args:
        app: Application executable name (e.g., "WINWORD.EXE")
        is_idle: Whether this is an idle period

    Returns:
        Hex color string (e.g., "#4285F4")
    """
    if is_idle or app is None:
        return IDLE_COLOR

    if app not in _app_color_cache:
        # Hash app name to get consistent index
        hash_val = int(hashlib.md5(app.encode()).hexdigest(), 16)
        color_index = hash_val % len(APP_COLORS)
        _app_color_cache[app] = APP_COLORS[color_index]

    return _app_color_cache[app]
