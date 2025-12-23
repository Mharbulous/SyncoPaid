"""
Events table schema and migration management.

Handles:
- Creating events table with all activity tracking fields
- Adding indices for query performance
- Schema migrations for backward compatibility
"""

import logging


class EventsSchemaMixin:
    """
    Mixin providing events table schema initialization and migrations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def _create_events_table(self, cursor):
        """
        Create events table if it doesn't exist.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                duration_seconds REAL,
                end_time TEXT,
                app TEXT,
                title TEXT,
                url TEXT,
                is_idle INTEGER DEFAULT 0
            )
        """)

    def _migrate_events_table(self, cursor):
        """
        Apply migrations to events table for backward compatibility.

        Args:
            cursor: Database cursor for executing migrations
        """
        # Get current columns
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]

        # Migration: Add end_time column if it doesn't exist
        if 'end_time' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN end_time TEXT")
            logging.info("Database migration: Added end_time column to events table")

        # Migration: Add state column if it doesn't exist
        if 'state' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN state TEXT DEFAULT 'Active'")
            logging.info("Database migration: Added state column to events table")

            # Backfill existing data: set state based on is_idle
            cursor.execute("""
                UPDATE events
                SET state = CASE WHEN is_idle = 1 THEN 'Inactive' ELSE 'Active' END
                WHERE state IS NULL
            """)
            logging.info("Database migration: Backfilled state column from is_idle")

        # Migration: Add metadata column if it doesn't exist
        if 'metadata' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN metadata TEXT")
            logging.info("Database migration: Added metadata column to events table")

        # Migration: Add cmdline column if it doesn't exist
        if 'cmdline' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN cmdline TEXT")
            logging.info("Database migration: Added cmdline column to events table")

        # Migration: Add interaction_level column if it doesn't exist
        if 'interaction_level' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN interaction_level TEXT DEFAULT 'passive'")
            logging.info("Database migration: Added interaction_level column to events table")

        # Migration: Add categorization columns if they don't exist
        if 'matter_id' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN matter_id INTEGER")
            logging.info("Database migration: Added matter_id column to events table")

        if 'confidence' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN confidence INTEGER DEFAULT 0")
            logging.info("Database migration: Added confidence column to events table")

        if 'flagged_for_review' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN flagged_for_review INTEGER DEFAULT 0")
            logging.info("Database migration: Added flagged_for_review column to events table")

        # Migration: Add client column for time assignment
        if 'client' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN client TEXT")
            logging.info("Database migration: Added client column to events table")

        # Migration: Add matter column for time assignment
        if 'matter' not in columns:
            cursor.execute("ALTER TABLE events ADD COLUMN matter TEXT")
            logging.info("Database migration: Added matter column to events table")

    def _create_events_indices(self, cursor):
        """
        Create database indices for events table query performance.

        Args:
            cursor: Database cursor for creating indices
        """
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON events(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_app
            ON events(app)
        """)
