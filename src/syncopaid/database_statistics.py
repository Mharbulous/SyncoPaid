"""
Database statistics and reporting operations.

Provides methods for generating statistics, summaries, and formatting
duration values for human-readable display.
"""

import logging
from typing import Dict
from datetime import datetime


class StatisticsDatabaseMixin:
    """
    Mixin class providing statistics and reporting database operations.

    Must be mixed with a class that provides:
    - self._get_connection(): Context manager for database connections
    - self.get_events(): Method to query events
    """

    def get_statistics(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dictionary with:
            - total_events: Total number of events
            - total_duration_seconds: Sum of all durations
            - active_duration_seconds: Sum of non-idle durations
            - idle_duration_seconds: Sum of idle durations
            - first_event: Timestamp of earliest event
            - last_event: Timestamp of most recent event
            - date_range_days: Number of days covered
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get counts and durations
            cursor.execute("""
                SELECT
                    COUNT(*) as total_events,
                    SUM(duration_seconds) as total_duration,
                    SUM(CASE WHEN is_idle = 0 THEN duration_seconds ELSE 0 END) as active_duration,
                    SUM(CASE WHEN is_idle = 1 THEN duration_seconds ELSE 0 END) as idle_duration,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM events
            """)

            row = cursor.fetchone()

            # Calculate date range
            date_range_days = 0
            if row['first_event'] and row['last_event']:
                first = datetime.fromisoformat(row['first_event'])
                last = datetime.fromisoformat(row['last_event'])
                date_range_days = (last - first).days + 1

            return {
                'total_events': row['total_events'] or 0,
                'total_duration_seconds': row['total_duration'] or 0.0,
                'active_duration_seconds': row['active_duration'] or 0.0,
                'idle_duration_seconds': row['idle_duration'] or 0.0,
                'first_event': row['first_event'],
                'last_event': row['last_event'],
                'date_range_days': date_range_days
            }

    def get_daily_summary(self, target_date: str) -> Dict:
        """
        Get summary statistics for a specific day.

        Args:
            target_date: ISO date string (YYYY-MM-DD)

        Returns:
            Dictionary with daily statistics
        """
        events = self.get_events(start_date=target_date, end_date=target_date)

        total_duration = sum(e['duration_seconds'] for e in events)
        active_duration = sum(e['duration_seconds'] for e in events if not e['is_idle'])
        idle_duration = sum(e['duration_seconds'] for e in events if e['is_idle'])

        # Count unique apps
        unique_apps = len(set(e['app'] for e in events if e['app']))

        return {
            'date': target_date,
            'total_events': len(events),
            'total_duration_seconds': total_duration,
            'active_duration_seconds': active_duration,
            'idle_duration_seconds': idle_duration,
            'unique_applications': unique_apps
        }


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "2h 15m" or "45m" or "30s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds / 60)
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"

    return f"{hours}h {remaining_minutes}m"
