"""
Database schema initialization and migration management.

Handles:
- Creating tables and indices
- Schema migrations for new columns
- Backward compatibility for existing databases
"""

import logging


class SchemaMixin:
    """
    Mixin providing schema initialization and migration logic.

    Requires _get_connection() method from ConnectionMixin.
    """

    def _init_schema(self):
        """
        Create database schema if it doesn't exist.

        Schema includes:
        - events table with all activity fields
        - screenshots table with captured screenshots metadata
        - Indices on timestamp and app for query performance
        - Automatic migrations for schema updates
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create events table
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

            # Run migrations to add columns for existing databases
            self._migrate_events_table(cursor)

            # Create indices for query performance
            self._create_indices(cursor)

            # Create screenshots table
            self._create_screenshots_table(cursor)

            logging.info("Database schema initialized")

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

    def _create_indices(self, cursor):
        """
        Create database indices for query performance.

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

    def _create_screenshots_table(self, cursor):
        """
        Create screenshots table and related indices.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                file_path TEXT NOT NULL,
                window_app TEXT,
                window_title TEXT,
                dhash TEXT
            )
        """)

        # Create index for screenshots timestamp queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_screenshots_time
            ON screenshots(captured_at)
        """)
