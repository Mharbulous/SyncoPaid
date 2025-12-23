"""
Database operations for AI categorization learning patterns.

Patterns are created from user corrections when they change AI categorization
suggestions. Each pattern maps activity attributes (app, URL, title) to a matter.

This module combines CRUD operations, learning logic, and export functionality.
"""

from .database_patterns_crud import PatternsCRUDMixin
from .database_patterns_learning import PatternsLearningMixin
from .database_patterns_export import PatternsExportMixin


class PatternsDatabaseMixin(PatternsCRUDMixin, PatternsLearningMixin, PatternsExportMixin):
    """
    Mixin providing categorization pattern operations.

    Combines:
    - PatternsCRUDMixin: Basic create, read, update, delete operations
    - PatternsLearningMixin: User correction recording and pattern learning
    - PatternsExportMixin: Pattern maintenance and JSON export

    Requires _get_connection() method from ConnectionMixin.
    """

    @staticmethod
    def _dict_factory(cursor, row):
        """Convert SQLite row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
