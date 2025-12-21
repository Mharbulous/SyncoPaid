"""
Event finalization and creation logic for TrackerLoop.

Converts tracked state into ActivityEvent objects ready for storage.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from syncopaid.tracker_state import (
    ActivityEvent,
    InteractionLevel,
    STATE_ACTIVE,
    STATE_INACTIVE,
    STATE_OFF
)


class EventFinalizer:
    """
    Finalizes tracked events into ActivityEvent objects.

    Takes the current tracked state and converts it into a properly
    formatted ActivityEvent with timestamps, duration, and metadata.
    """

    def __init__(self, ui_automation_worker=None):
        """
        Initialize event finalizer.

        Args:
            ui_automation_worker: Optional worker for extracting UI metadata
        """
        self.ui_automation_worker = ui_automation_worker
        self.total_events: int = 0

    def finalize_event(
        self,
        current_event: Optional[Dict],
        event_start_time: Optional[datetime]
    ) -> Optional[ActivityEvent]:
        """
        Convert the current tracked event into an ActivityEvent object.

        Args:
            current_event: The state dictionary for the current event
            event_start_time: When the event started

        Returns:
            ActivityEvent ready for storage, or None if event is invalid/too short
        """
        if not current_event or not event_start_time:
            return None

        # Calculate duration and end time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - event_start_time).total_seconds()

        # Skip events that are too short (< 0.5 seconds)
        if duration < 0.5:
            return None

        # Determine state: locked/screensaver > idle > active
        if current_event.get('is_locked_or_screensaver', False):
            event_state = STATE_OFF
        elif current_event.get('is_idle', False):
            event_state = STATE_INACTIVE
        else:
            event_state = STATE_ACTIVE

        # Extract metadata if UI automation worker is configured
        metadata = None
        if self.ui_automation_worker and 'window_info' in current_event:
            metadata = self.ui_automation_worker.extract(current_event['window_info'])

        # Create event with start time, duration, end time, state, and interaction level
        event = ActivityEvent(
            timestamp=event_start_time.isoformat(),
            duration_seconds=round(duration, 2),
            app=current_event['app'],
            title=current_event['title'],
            end_time=end_time.isoformat(),
            url=current_event.get('url'),  # Extracted context (URL, subject, or filepath)
            cmdline=current_event.get('cmdline'),  # Process command line arguments
            is_idle=current_event['is_idle'],
            state=event_state,
            interaction_level=current_event.get('interaction_level', InteractionLevel.PASSIVE.value),
            metadata=metadata
        )

        self.total_events += 1
        return event
