"""
Database CRUD operations for categorization patterns.

Provides basic create, read, update, and delete operations for AI categorization
learning patterns. Each pattern maps activity attributes (app, URL, title) to a matter.
"""

import logging
from typing import List, Dict, Optional


class PatternsCRUDMixin:
    """
    Mixin providing basic CRUD operations for categorization patterns.

    Requires _get_connection() and _dict_factory() methods.
    """

    def insert_pattern(
        self,
        matter_id: int,
        app_pattern: Optional[str] = None,
        url_pattern: Optional[str] = None,
        title_pattern: Optional[str] = None,
        confidence_score: float = 1.0
    ) -> int:
        """
        Insert a new categorization pattern.

        Args:
            matter_id: ID of the matter this pattern maps to
            app_pattern: Application name pattern (exact or wildcard)
            url_pattern: URL pattern (supports wildcards)
            title_pattern: Window title pattern (supports wildcards)
            confidence_score: Initial confidence (0.0-1.0)

        Returns:
            ID of the inserted pattern
        """
        if not any([app_pattern, url_pattern, title_pattern]):
            raise ValueError("At least one pattern (app, url, or title) is required")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categorization_patterns
                (matter_id, app_pattern, url_pattern, title_pattern, confidence_score)
                VALUES (?, ?, ?, ?, ?)
            """, (matter_id, app_pattern, url_pattern, title_pattern, confidence_score))
            conn.commit()
            logging.debug(f"Inserted pattern {cursor.lastrowid} for matter {matter_id}")
            return cursor.lastrowid

    def get_patterns_for_matter(self, matter_id: int, include_archived: bool = False) -> List[Dict]:
        """
        Get all patterns for a specific matter.

        Args:
            matter_id: ID of the matter
            include_archived: Whether to include archived patterns

        Returns:
            List of pattern dictionaries
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            if include_archived:
                cursor.execute("""
                    SELECT * FROM categorization_patterns
                    WHERE matter_id = ?
                    ORDER BY confidence_score DESC, last_used_at DESC
                """, (matter_id,))
            else:
                cursor.execute("""
                    SELECT * FROM categorization_patterns
                    WHERE matter_id = ? AND is_archived = 0
                    ORDER BY confidence_score DESC, last_used_at DESC
                """, (matter_id,))

            return cursor.fetchall()

    def find_matching_patterns(
        self,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> List[Dict]:
        """
        Find patterns matching the given activity attributes.

        Uses exact matching for app_pattern and LIKE matching for url/title.
        Returns patterns sorted by confidence score descending.

        Args:
            app: Application name to match
            url: URL to match
            title: Window title to match

        Returns:
            List of matching pattern dicts with matter_id and confidence_score
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            conditions = ["is_archived = 0"]
            params = []

            # Build OR conditions for pattern matching
            pattern_conditions = []

            if app:
                pattern_conditions.append("(app_pattern IS NOT NULL AND app_pattern = ?)")
                params.append(app)

            if url:
                pattern_conditions.append("(url_pattern IS NOT NULL AND ? LIKE REPLACE(REPLACE(url_pattern, '*', '%'), '?', '_'))")
                params.append(url)

            if title:
                pattern_conditions.append("(title_pattern IS NOT NULL AND ? LIKE REPLACE(REPLACE(title_pattern, '*', '%'), '?', '_'))")
                params.append(title)

            if not pattern_conditions:
                return []

            conditions.append(f"({' OR '.join(pattern_conditions)})")

            query = f"""
                SELECT cp.*, m.display_name as matter_display_name
                FROM categorization_patterns cp
                JOIN matters m ON cp.matter_id = m.id
                WHERE {' AND '.join(conditions)}
                ORDER BY cp.confidence_score DESC, cp.match_count DESC
            """

            cursor.execute(query, params)
            return cursor.fetchall()

    def delete_pattern(self, pattern_id: int) -> bool:
        """
        Delete a pattern by ID.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorization_patterns WHERE id = ?", (pattern_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_patterns(self, include_archived: bool = False) -> List[Dict]:
        """
        Get all patterns across all matters.

        Args:
            include_archived: Whether to include archived patterns

        Returns:
            List of all pattern dictionaries with matter info
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            archive_filter = "" if include_archived else "WHERE cp.is_archived = 0"

            cursor.execute(f"""
                SELECT cp.*, m.display_name as matter_description,
                       c.display_name as client_name
                FROM categorization_patterns cp
                JOIN matters m ON cp.matter_id = m.id
                LEFT JOIN clients c ON m.client_id = c.id
                {archive_filter}
                ORDER BY cp.confidence_score DESC, cp.match_count DESC
            """)
            return cursor.fetchall()
