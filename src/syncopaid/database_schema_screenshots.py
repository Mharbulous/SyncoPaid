"""
Screenshots and transitions table schema management.

Handles:
- Creating screenshots table with metadata tracking
- Creating transitions table for timing patterns
- Schema migrations for analysis features
"""

import logging


class ScreenshotsSchemaMixin:
    """
    Mixin providing screenshots and transitions table schema.

    Requires _get_connection() method from ConnectionMixin.
    """

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

    def _migrate_screenshots_table(self):
        """Apply migrations to screenshots table for analysis support."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'analysis_data' not in columns:
                cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_data TEXT")
                logging.info("Migration: Added analysis_data column to screenshots")

            if 'analysis_status' not in columns:
                cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_status TEXT DEFAULT 'pending'")
                logging.info("Migration: Added analysis_status column to screenshots")

            conn.commit()

    def _create_transitions_table(self, cursor):
        """
        Create transitions table for tracking timing patterns.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                transition_type TEXT NOT NULL,
                context TEXT,
                user_response TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for transitions timestamp queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transitions_timestamp
            ON transitions(timestamp)
        """)
