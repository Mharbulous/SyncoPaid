"""
Database update operations for activity events.

Provides:
- Update event categorization
"""

import logging
from typing import Optional


class EventUpdateMixin:
    """
    Mixin providing event update operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def update_event_categorization(
        self,
        event_id: int,
        matter_id: Optional[int] = None,
        confidence: int = 100,
        flagged_for_review: bool = False
    ):
        """Update categorization of an existing event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events
                SET matter_id = ?, confidence = ?, flagged_for_review = ?
                WHERE id = ?
            """, (matter_id, confidence, 1 if flagged_for_review else 0, event_id))

            logging.info(f"Updated categorization for event {event_id}")
