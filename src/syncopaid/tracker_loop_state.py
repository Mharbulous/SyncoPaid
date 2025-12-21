"""
State change detection and merging logic for TrackerLoop.

Determines when window states have changed and whether to merge
brief window switches into a single continuous event.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional


class StateChangeDetector:
    """
    Detects state changes and handles event merging.

    Tracks the current window state and determines when it has changed
    sufficiently to warrant creating a new event. Implements merge logic
    to avoid creating events for brief accidental window switches.
    """

    def __init__(self, merge_threshold: float = 2.0):
        """
        Initialize state change detector.

        Args:
            merge_threshold: Max gap (seconds) to merge identical windows
        """
        self.merge_threshold = merge_threshold
        self.current_event: Optional[Dict] = None
        self.event_start_time: Optional[datetime] = None
        self.merged_events: int = 0
        self._was_locked: bool = False

    def has_state_changed(self, new_state: Dict) -> bool:
        """
        Check if the current state is different from the tracked state.

        Considers the merge_threshold: if user briefly switches windows
        but returns within merge_threshold seconds, treat as continuous.

        Args:
            new_state: The new state dictionary to compare

        Returns:
            True if state has changed enough to warrant a new event
        """
        if self.current_event is None:
            return True

        # Check if core attributes changed
        if (new_state['app'] != self.current_event['app'] or
            new_state['title'] != self.current_event['title'] or
            new_state['is_idle'] != self.current_event['is_idle'] or
            new_state.get('is_locked_or_screensaver', False) != self.current_event.get('is_locked_or_screensaver', False)):

            # State changed - check if within merge threshold
            if self.event_start_time:
                elapsed = (datetime.now(timezone.utc) - self.event_start_time).total_seconds()
                if elapsed < self.merge_threshold:
                    # Too quick - might be accidental switch, merge it
                    self.merged_events += 1
                    return False

            return True

        return False

    def start_new_event(self, state: Dict) -> None:
        """
        Start tracking a new event with the given state.

        Args:
            state: The state dictionary for the new event
        """
        self.current_event = state
        self.event_start_time = datetime.now(timezone.utc)

    def log_lock_transitions(self, is_locked_or_screensaver: bool) -> None:
        """
        Log lock screen and screensaver transitions for debugging.

        Args:
            is_locked_or_screensaver: Whether workstation is locked or screensaver is active
        """
        if is_locked_or_screensaver:
            if not self._was_locked:
                logging.info("Workstation locked/screensaver active - switching to STATE_OFF")
                self._was_locked = True
        else:
            if self._was_locked:
                logging.info("Workstation unlocked/screensaver deactivated - resuming tracking")
                self._was_locked = False
