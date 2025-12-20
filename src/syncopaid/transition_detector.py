"""
Transition pattern detection for identifying natural break points.

Detects:
- Inbox browsing (email checking)
- Idle return (coming back from break)
- File explorer navigation
- Context switches
"""

from typing import Optional


class TransitionDetector:
    """Detects transition points between tasks based on activity patterns."""

    INBOX_KEYWORDS = ["inbox", "- outlook", "mail"]
    EXPLORER_KEYWORDS = ["file explorer", "documents", "downloads"]
    ACTIVE_EDIT_APPS = ["winword.exe", "excel.exe", "acrord32.exe"]
    IDLE_THRESHOLD = 300  # 5 minutes

    def __init__(self):
        self.last_transition_type: Optional[str] = None

    def is_transition(
        self,
        app: str,
        title: str,
        prev_app: Optional[str],
        prev_title: Optional[str],
        idle_seconds: float
    ) -> bool:
        """
        Determine if current activity represents a transition point.

        Args:
            app: Current application name
            title: Current window title
            prev_app: Previous application name (or None)
            prev_title: Previous window title (or None)
            idle_seconds: Seconds of idle time before this activity

        Returns:
            True if transition detected, False otherwise.
            Sets self.last_transition_type to the type detected.
        """
        # Never interrupt active document editing
        if app and app.lower() in self.ACTIVE_EDIT_APPS:
            if prev_app and prev_app.lower() == app.lower():
                return False

        # Idle return (5+ minutes)
        if idle_seconds >= self.IDLE_THRESHOLD:
            self.last_transition_type = "idle_return"
            return True

        # Inbox browsing
        if title and any(kw in title.lower() for kw in self.INBOX_KEYWORDS):
            if prev_title and not any(kw in prev_title.lower() for kw in self.INBOX_KEYWORDS):
                self.last_transition_type = "inbox_browsing"
                return True

        # File Explorer navigation
        if title and any(kw in title.lower() for kw in self.EXPLORER_KEYWORDS):
            if prev_app != app:
                self.last_transition_type = "explorer_navigation"
                return True

        return False
