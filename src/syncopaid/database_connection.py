"""
Database connection management for SQLite operations.

Provides:
- Connection context manager with automatic commit/rollback
- Row factory configuration for column access by name
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path


class ConnectionMixin:
    """
    Mixin providing database connection management.

    Requires self.db_path to be set by the using class.
    """

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Features:
        - Automatic commit on success
        - Automatic rollback on exception
        - Row factory for column access by name
        - Proper connection cleanup

        Yields:
            sqlite3.Connection: Database connection with row factory
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _ensure_db_directory(self):
        """
        Ensure the database directory exists.

        Creates parent directories as needed.
        """
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
