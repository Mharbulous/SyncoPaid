"""
Database CRUD operations for activity events.

Provides:
- Insert single or batch events
- Query events with filtering
- Delete events by date range or IDs
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .tracker import ActivityEvent


class EventOperationsMixin:
    """
    Mixin providing event-related database CRUD operations.

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

    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_idle: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query events with optional filtering.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            include_idle: Whether to include idle events (default True)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND timestamp < ?"
                # Add one day to make end_date inclusive
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            if not include_idle:
                query += " AND is_idle = 0"

            query += " ORDER BY timestamp ASC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            # Convert rows to dictionaries
            return self._rows_to_dicts(cursor.fetchall())

    def delete_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        Delete events within a date range.

        CAUTION: This permanently removes data. Use carefully.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)

        Returns:
            Number of events deleted
        """
        if not start_date and not end_date:
            raise ValueError("Must specify at least start_date or end_date")

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build delete query
            query = "DELETE FROM events WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND timestamp < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            cursor.execute(query, params)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events from database")
            return deleted_count

    def delete_events_by_ids(self, event_ids: List[int]) -> int:
        """
        Delete specific events by their IDs.

        Args:
            event_ids: List of event IDs to delete

        Returns:
            Number of events deleted
        """
        if not event_ids:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use parameterized query with placeholders
            placeholders = ','.join('?' * len(event_ids))
            query = f"DELETE FROM events WHERE id IN ({placeholders})"

            cursor.execute(query, event_ids)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events by ID from database")
            return deleted_count

    def _rows_to_dicts(self, rows) -> List[Dict]:
        """
        Convert database rows to dictionaries with backward compatibility.

        Args:
            rows: Database rows with row factory

        Returns:
            List of event dictionaries
        """
        events = []
        for row in rows:
            # Derive state from is_idle if column doesn't exist (backward compatibility)
            if 'state' in row.keys() and row['state']:
                state = row['state']
            else:
                state = 'Inactive' if row['is_idle'] else 'Active'

            # Deserialize metadata JSON if present
            metadata = None
            if 'metadata' in row.keys() and row['metadata']:
                metadata = json.loads(row['metadata'])

            # Get cmdline field if it exists (backward compatibility)
            cmdline = row['cmdline'] if 'cmdline' in row.keys() else None

            # Get interaction_level with fallback for older records
            if 'interaction_level' in row.keys() and row['interaction_level']:
                interaction_level = row['interaction_level']
            else:
                interaction_level = 'passive'

            events.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'duration_seconds': row['duration_seconds'],
                'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                'app': row['app'],
                'title': row['title'],
                'url': row['url'],
                'cmdline': cmdline,
                'is_idle': bool(row['is_idle']),
                'state': state,
                'metadata': metadata,
                'interaction_level': interaction_level
            })

        return events
