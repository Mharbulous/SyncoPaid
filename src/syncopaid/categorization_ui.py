"""
Screenshot-assisted time categorization UI components.

Provides UI components for displaying screenshots during the categorization
flow when AI confidence is low.
"""

from typing import List, Dict


def query_screenshots_for_activity(db, start_time: str, end_time: str) -> List[Dict]:
    """Query screenshots within activity timestamp range."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, captured_at, file_path, window_app, window_title
            FROM screenshots
            WHERE captured_at >= ? AND captured_at <= ?
            ORDER BY captured_at ASC
        """, (start_time, end_time))
        return [dict(row) for row in cursor.fetchall()]
