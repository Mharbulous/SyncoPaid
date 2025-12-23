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

            # Create transitions table
            self._create_transitions_table(cursor)

            # Create clients and matters tables
            self._create_clients_table(cursor)
            self._create_matters_table(cursor)

            # Create matter keywords table for AI keyword extraction
            self._create_matter_keywords_table(cursor)

            # Create categorization patterns table for AI learning
            self._create_categorization_patterns_table(cursor)

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
