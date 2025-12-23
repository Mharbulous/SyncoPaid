"""
Client and matter management schema.

Handles:
- Creating clients and matters tables for legal matter tracking
- Creating matter keywords table for AI-managed keyword extraction
- Creating categorization patterns table for AI learning
"""

import logging


class MattersSchemaMixin:
    """
    Mixin providing matter-related table schema.

    Requires _get_connection() method from ConnectionMixin.
    """

    def _create_clients_table(self, cursor):
        """Create clients table for imported client folder names."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                folder_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(display_name)
            )
        """)
        logging.debug("Ensured clients table exists")

    def _migrate_clients_table(self, cursor):
        """
        Apply migrations to clients table for backward compatibility.

        Handles schema evolution from older versions that used 'name' column
        to the current schema using 'display_name' and 'folder_path'.

        Args:
            cursor: Database cursor for executing migrations
        """
        # Check if clients table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='clients'"
        )
        if not cursor.fetchone():
            return  # Table doesn't exist yet, nothing to migrate

        # Get current columns
        cursor.execute("PRAGMA table_info(clients)")
        columns = [row[1] for row in cursor.fetchall()]

        # Migration: Add display_name column if missing (migrate from 'name')
        if 'display_name' not in columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN display_name TEXT")
            logging.info(
                "Database migration: Added display_name column to clients table"
            )

            # If old 'name' column exists, migrate data from it
            if 'name' in columns:
                cursor.execute(
                    "UPDATE clients SET display_name = name WHERE display_name IS NULL"
                )
                logging.info(
                    "Database migration: Migrated data from name to display_name"
                )

        # Migration: Add folder_path column if missing
        if 'folder_path' not in columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN folder_path TEXT")
            logging.info(
                "Database migration: Added folder_path column to clients table"
            )

    def _create_matters_table(self, cursor):
        """Create matters table for imported matter folder names."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                folder_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                UNIQUE(client_id, display_name)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_matters_client ON matters(client_id)"
        )
        logging.debug("Ensured matters table exists")

    def _create_matter_keywords_table(self, cursor):
        """
        Create matter_keywords table for AI-managed keyword extraction.

        Keywords are extracted and managed by AI - users cannot edit directly.
        This ensures keyword quality and avoids human error in categorization.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matter_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matter_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'ai',
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (matter_id) REFERENCES matters(id) ON DELETE CASCADE,
                UNIQUE(matter_id, keyword)
            )
        """)

        # Create index for efficient keyword lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matter_keywords_matter
            ON matter_keywords(matter_id)
        """)

        # Create index for keyword search across all matters
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matter_keywords_keyword
            ON matter_keywords(keyword)
        """)
        logging.debug("Ensured matter_keywords table exists")

    def _create_categorization_patterns_table(self, cursor):
        """
        Create categorization_patterns table for AI learning.

        Stores user corrections to build matter-specific patterns that
        improve categorization accuracy over time. Patterns match on
        app name, URL, and/or window title.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorization_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matter_id INTEGER NOT NULL,
                app_pattern TEXT,
                url_pattern TEXT,
                title_pattern TEXT,
                confidence_score REAL NOT NULL DEFAULT 1.0,
                match_count INTEGER NOT NULL DEFAULT 1,
                correction_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_used_at TEXT NOT NULL DEFAULT (datetime('now')),
                is_archived INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (matter_id) REFERENCES matters(id) ON DELETE CASCADE
            )
        """)

        # Index for efficient pattern lookups during categorization
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_app
            ON categorization_patterns(app_pattern)
            WHERE app_pattern IS NOT NULL AND is_archived = 0
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_matter
            ON categorization_patterns(matter_id)
            WHERE is_archived = 0
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_last_used
            ON categorization_patterns(last_used_at)
            WHERE is_archived = 0
        """)
