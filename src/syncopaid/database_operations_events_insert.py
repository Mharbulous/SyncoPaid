"""
Database insert operations for activity events.

Provides:
- Insert single or batch events
"""

import json
import logging
from typing import List, Optional

from .tracker import ActivityEvent


class EventInsertMixin:
    """
    Mixin providing event insert operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def insert_event(
        self,
        event: ActivityEvent,
        matter_id: Optional[int] = None,
        confidence: int = 0,
        flagged_for_review: bool = False
    ) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store
            matter_id: Optional matter ID for categorization
            confidence: Confidence score (0-100) for matter assignment
            flagged_for_review: Whether event needs manual review

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')
            metadata = getattr(event, 'metadata', None)
            cmdline = getattr(event, 'cmdline', None)
            interaction_level = getattr(event, 'interaction_level', 'passive')

            # Serialize metadata to JSON if present
            metadata_json = json.dumps(metadata) if metadata else None

            # Serialize cmdline to JSON
            cmdline_json = json.dumps(cmdline) if cmdline else None

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline,
                                  is_idle, state, metadata, interaction_level,
                                  matter_id, confidence, flagged_for_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                cmdline_json,
                1 if event.is_idle else 0,
                state,
                metadata_json,
                interaction_level,
                matter_id,
                confidence,
                1 if flagged_for_review else 0
            ))

            return cursor.lastrowid

    def insert_events_batch(self, events: List[ActivityEvent]) -> int:
        """
        Insert multiple events in a single transaction (more efficient).

        Args:
            events: List of ActivityEvent objects

        Returns:
            Number of events inserted
        """
        if not events:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline, is_idle, state, metadata, interaction_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url,
                 json.dumps(getattr(e, 'cmdline', None)) if getattr(e, 'cmdline', None) else None,
                 1 if e.is_idle else 0, getattr(e, 'state', 'Active'),
                 json.dumps(getattr(e, 'metadata', None)) if getattr(e, 'metadata', None) else None,
                 getattr(e, 'interaction_level', 'passive'))
                for e in events
            ])

            return len(events)
