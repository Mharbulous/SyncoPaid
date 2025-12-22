"""
Database query operations for activity events.

Provides:
- Query events with filtering
- Get flagged events
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime


class EventQueryMixin:
    """
    Mixin providing event query operations.

    Requires _get_connection() and _rows_to_dicts() methods.
    """

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

    def get_flagged_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get events flagged for manual review."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM events WHERE flagged_for_review = 1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            query += " ORDER BY timestamp ASC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            events = []
            for row in cursor.fetchall():
                state = row['state'] if 'state' in row.keys() and row['state'] else ('Inactive' if row['is_idle'] else 'Active')
                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'duration_seconds': row['duration_seconds'],
                    'app': row['app'],
                    'title': row['title'],
                    'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
                    'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
                    'flagged_for_review': True,
                })

            return events
