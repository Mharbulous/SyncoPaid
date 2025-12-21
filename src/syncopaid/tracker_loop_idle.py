"""
Idle state tracking and resumption event generation for TrackerLoop.

Handles detection of idle periods and generation of idle resumption events
when the user returns to active usage.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from syncopaid.tracker_state import IdleResumptionEvent


class IdleTracker:
    """
    Tracks idle state transitions and generates resumption events.

    This class monitors when users go idle and return to active usage,
    generating IdleResumptionEvent objects when appropriate.
    """

    def __init__(self, minimum_idle_duration: float = 180.0):
        """
        Initialize idle tracker.

        Args:
            minimum_idle_duration: Minimum idle time (seconds) before generating
                                   a resumption event
        """
        self.minimum_idle_duration = minimum_idle_duration
        self.was_idle: bool = False
        self.last_idle_resumption_time: Optional[datetime] = None
        self._peak_idle_seconds: float = 0.0

    def update_idle_state(self, is_idle: bool, idle_seconds: float) -> Optional[IdleResumptionEvent]:
        """
        Update idle state and potentially generate a resumption event.

        Args:
            is_idle: Whether the user is currently idle
            idle_seconds: How many seconds the user has been idle

        Returns:
            IdleResumptionEvent if user just resumed from significant idle period,
            None otherwise
        """
        resumption_event = None

        # Detect idle→active transition for resumption events
        if self.was_idle and not is_idle:
            # User just resumed after idle period
            if self._peak_idle_seconds >= self.minimum_idle_duration:
                # Check if enough time passed since last resumption (prevent duplicates)
                should_emit = True
                if self.last_idle_resumption_time:
                    time_since_last = (datetime.now(timezone.utc) - self.last_idle_resumption_time).total_seconds()
                    # Only emit if at least 60 seconds passed since last resumption
                    # This prevents rapid fire events from flaky idle detection
                    if time_since_last < 60.0:
                        should_emit = False
                        logging.debug(f"Suppressing duplicate resumption event (last: {time_since_last:.1f}s ago)")

                if should_emit:
                    idle_minutes = self._peak_idle_seconds / 60.0
                    resumption_event = IdleResumptionEvent(
                        resumption_timestamp=datetime.now(timezone.utc).isoformat(),
                        idle_duration=self._peak_idle_seconds
                    )
                    logging.info(f"User resumed after {idle_minutes:.1f} minutes idle")
                    self.last_idle_resumption_time = datetime.now(timezone.utc)

                # Always reset peak after processing transition
                self._peak_idle_seconds = 0.0

        # Track idle state for next iteration
        if is_idle and not self.was_idle:
            # Just became idle - start tracking peak
            self._peak_idle_seconds = idle_seconds
            logging.debug(f"User went idle (idle_seconds={idle_seconds:.1f}s)")
        elif is_idle:
            # Still idle - update peak
            self._peak_idle_seconds = max(self._peak_idle_seconds, idle_seconds)

        self.was_idle = is_idle
        return resumption_event
