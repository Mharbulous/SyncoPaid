"""
Interaction level detection for tracking loop.

Determines the level of user interaction based on keyboard and mouse activity.
"""

import logging
from datetime import datetime, timezone

from syncopaid.tracker_state import InteractionLevel
from syncopaid.tracker_windows import get_keyboard_activity, get_mouse_activity


class InteractionLevelDetector:
    """
    Detects and tracks user interaction levels.

    Monitors keyboard and mouse activity to determine if the user is:
    - IDLE: No activity for idle_threshold seconds
    - TYPING: Recent keyboard activity detected
    - CLICKING: Recent mouse activity detected
    - PASSIVE: Reading or passive reference (no activity)
    """

    def __init__(self, idle_threshold: float = 180.0, interaction_threshold: float = 5.0):
        """
        Initialize the interaction level detector.

        Args:
            idle_threshold: Seconds before marking as idle
            interaction_threshold: Seconds to consider activity as "recent"
        """
        self.idle_threshold = idle_threshold
        self.interaction_threshold = interaction_threshold
        self.last_typing_time = None
        self.last_click_time = None

    def get_interaction_level(self, idle_seconds: float) -> InteractionLevel:
        """
        Determine current interaction level based on activity state.

        Updates internal tracking timestamps when activity is detected.

        Priority order:
        1. IDLE if globally idle (idle_seconds >= idle_threshold)
        2. TYPING if keyboard activity detected or recent
        3. CLICKING if mouse activity detected or recent
        4. PASSIVE if none of the above

        Args:
            idle_seconds: Current global idle time from GetLastInputInfo

        Returns:
            InteractionLevel enum value
        """
        now = datetime.now(timezone.utc)

        # Check if globally idle first
        if idle_seconds >= self.idle_threshold:
            return InteractionLevel.IDLE

        # Check for current keyboard activity
        if get_keyboard_activity():
            self.last_typing_time = now
            return InteractionLevel.TYPING

        # Check for current mouse activity
        if get_mouse_activity():
            self.last_click_time = now
            return InteractionLevel.CLICKING

        # Check if recent typing (within threshold)
        if self.last_typing_time:
            typing_age = (now - self.last_typing_time).total_seconds()
            if typing_age < self.interaction_threshold:
                return InteractionLevel.TYPING

        # Check if recent clicking (within threshold)
        if self.last_click_time:
            click_age = (now - self.last_click_time).total_seconds()
            if click_age < self.interaction_threshold:
                return InteractionLevel.CLICKING

        # No recent activity - passive reading/reference
        return InteractionLevel.PASSIVE
