"""
System tray icon state management.

Handles the state machine for tracking status (on/paused/inactive)
and icon refresh logic.
"""

import logging
from typing import Optional

try:
    import pystray
    from syncopaid.tray_icons import create_icon_image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Version info
try:
    from syncopaid import __product_version__
except ImportError:
    __product_version__ = "1.0.0"


class TrayStateManager:
    """
    Manages tray icon state transitions and icon rendering.

    State machine:
    - "on": Tracking active (green icon)
    - "paused": User manually paused (orange icon)
    - "inactive": No activity for 5+ min (faded icon)
    """

    def __init__(self):
        """Initialize state manager."""
        self.icon: Optional[pystray.Icon] = None
        self.is_tracking = True
        self.is_inactive = False  # True when no activity for 5 minutes

    def _get_current_state(self) -> str:
        """Get the current icon state based on tracking and inactive flags."""
        if not self.is_tracking:
            return "paused"
        elif self.is_inactive:
            return "inactive"
        else:
            return "on"

    def update_icon_status(self, is_tracking: bool):
        """
        Update icon based on tracking status (user pause/unpause).

        Args:
            is_tracking: True if tracking, False if user paused
        """
        self.is_tracking = is_tracking
        if is_tracking:
            self.is_inactive = False  # Clear inactive when user resumes

        self._refresh_icon()

    def set_inactive(self, inactive: bool):
        """
        Set inactive state (no activity detected for 5 minutes).

        This shows the faded icon with sleep emoji. Only applies when
        is_tracking is True (user hasn't manually paused).

        Args:
            inactive: True if no activity detected, False when activity resumes
        """
        if self.is_inactive != inactive:
            self.is_inactive = inactive
            if self.is_tracking:  # Only update if not manually paused
                self._refresh_icon()
                if inactive:
                    logging.info("User inactive - showing sleep icon")
                else:
                    logging.info("User active - showing normal icon")

    def _refresh_icon(self):
        """Refresh the icon based on current state."""
        if not TRAY_AVAILABLE:
            return

        if self.icon:
            state = self._get_current_state()
            self.icon.icon = create_icon_image(state)
            # Update tooltip to reflect state
            if state == "paused":
                self.icon.title = f"SyncoPaid v{__product_version__} - Paused"
            elif state == "inactive":
                self.icon.title = f"SyncoPaid v{__product_version__} - Inactive"
            else:
                self.icon.title = f"SyncoPaid v{__product_version__}"
