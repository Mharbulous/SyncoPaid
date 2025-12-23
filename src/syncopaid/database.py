"""
Database module for persistent storage of activity events.

Uses SQLite to store events locally with the following schema:
- events table with timestamp, duration, app, title, url, is_idle
- Indices on timestamp and app for efficient querying

All operations are local-only (no network access) to preserve
attorney-client privilege.
"""

import logging
from pathlib import Path

from .database_connection import ConnectionMixin
from .database_schema import SchemaMixin
from .database_operations import OperationsMixin
from .database_screenshots import ScreenshotDatabaseMixin
from .database_statistics import StatisticsDatabaseMixin, format_duration
from .database_keywords import KeywordsDatabaseMixin
from .database_patterns import PatternsDatabaseMixin


class Database(
    ConnectionMixin,
    SchemaMixin,
    OperationsMixin,
    ScreenshotDatabaseMixin,
    StatisticsDatabaseMixin,
    KeywordsDatabaseMixin,
    PatternsDatabaseMixin
):
    """
    SQLite database manager for activity events.

    Provides methods for:
    - Initializing database schema
    - Inserting captured events
    - Querying events by date range
    - Deleting events by date range
    - Database statistics
    - Screenshot management
    """

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Parent directory will
                    be created if it doesn't exist.
        """
        self.db_path = Path(db_path)

        # Ensure parent directory exists
        self._ensure_db_directory()

        # Initialize schema
        self._init_schema()

        logging.info(f"Database initialized: {self.db_path}")


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    import tempfile
    import os

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create test database
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_lawtime.db")
        print(f"Testing database: {test_db}\n")

        db = Database(test_db)

        # Create test events
        from .tracker import ActivityEvent

        test_events = [
            ActivityEvent(
                timestamp="2025-12-09T09:00:00",
                duration_seconds=300.0,
                app="WINWORD.EXE",
                title="Smith-Contract-v2.docx - Word",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:05:00",
                duration_seconds=600.0,
                app="chrome.exe",
                title="CanLII - 2024 BCSC 1234 - Google Chrome",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:15:00",
                duration_seconds=1800.0,
                app=None,
                title=None,
                is_idle=True
            ),
        ]

        # Insert test events
        print("Inserting test events...")
        count = db.insert_events_batch(test_events)
        print(f"✓ Inserted {count} events\n")

        # Query events
        print("Querying events...")
        events = db.get_events(start_date="2025-12-09")
        for event in events:
            idle_marker = "💤" if event['is_idle'] else "✓"
            duration_str = format_duration(event['duration_seconds'])
            print(f"  {idle_marker} {event['timestamp'][:19]} - {duration_str} - {event['app']} - {event['title']}")

        # Get statistics
        print("\nDatabase statistics:")
        stats = db.get_statistics()
        print(f"  Total events: {stats['total_events']}")
        print(f"  Active time: {format_duration(stats['active_duration_seconds'])}")
        print(f"  Idle time: {format_duration(stats['idle_duration_seconds'])}")

        # Get daily summary
        print("\nDaily summary for 2025-12-09:")
        summary = db.get_daily_summary("2025-12-09")
        print(f"  Events: {summary['total_events']}")
        print(f"  Active: {format_duration(summary['active_duration_seconds'])}")
        print(f"  Idle: {format_duration(summary['idle_duration_seconds'])}")

        print("\n✓ Database tests complete")
