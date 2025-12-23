"""
Database schema initialization and migration management.

Handles:
- Creating tables and indices
- Schema migrations for new columns
- Backward compatibility for existing databases
"""

import logging
from .database_schema_events import EventsSchemaMixin
from .database_schema_screenshots import ScreenshotsSchemaMixin
from .database_schema_matters import MattersSchemaMixin


class SchemaMixin(EventsSchemaMixin, ScreenshotsSchemaMixin, MattersSchemaMixin):
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
            self._create_events_table(cursor)

            # Run migrations to add columns for existing databases
            self._migrate_events_table(cursor)

            # Create indices for query performance
            self._create_events_indices(cursor)

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

        # Run migrations for screenshots table (outside cursor context)
        self._migrate_screenshots_table()

        logging.info("Database schema initialized")
