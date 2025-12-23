"""
Database delete operations for activity events.

Provides:
- Delete events by date range or IDs
"""

import logging
from typing import List, Optional
from datetime import datetime


class EventDeleteMixin:
    """
    Mixin providing event delete operations.

    Requires _get_connection() method from ConnectionMixin.
    """

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

    def delete_events_securely(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        Securely delete events and associated screenshots.

        Uses secure_delete pragma for database records and overwrites
        screenshot files before deletion.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start
            end_date: ISO date string (YYYY-MM-DD) for range end

        Returns:
            Number of events deleted
        """
        if not start_date and not end_date:
            raise ValueError("Must specify at least start_date or end_date")

        # First, find and delete associated screenshots
        # Screenshots are associated by timestamp overlap
        screenshots = self.get_screenshots(start_date=start_date, end_date=end_date)
        if screenshots:
            screenshot_ids = [s['id'] for s in screenshots]
            self.delete_screenshots_securely(screenshot_ids)

        # Then delete events (secure_delete pragma handles secure deletion)
        return self.delete_events(start_date=start_date, end_date=end_date)
