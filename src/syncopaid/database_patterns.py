"""
Database operations for AI categorization learning patterns.

Patterns are created from user corrections when they change AI categorization
suggestions. Each pattern maps activity attributes (app, URL, title) to a matter.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class PatternsDatabaseMixin:
    """
    Mixin providing categorization pattern operations.

    Requires _get_connection() method from ConnectionMixin.
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

    def record_correction(
        self,
        matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction to create or reinforce a pattern.

        When user corrects AI categorization, record the activity's attributes
        as a pattern for the correct matter. If pattern already exists,
        increase confidence and match count.

        Args:
            matter_id: Correct matter ID (what user selected)
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or updated pattern
        """
        if not any([app, url, title]):
            raise ValueError("At least one attribute (app, url, or title) is required")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Check if pattern already exists
            cursor.execute("""
                SELECT id, match_count, confidence_score
                FROM categorization_patterns
                WHERE matter_id = ?
                AND (app_pattern = ? OR (app_pattern IS NULL AND ? IS NULL))
                AND (url_pattern = ? OR (url_pattern IS NULL AND ? IS NULL))
                AND (title_pattern = ? OR (title_pattern IS NULL AND ? IS NULL))
                AND is_archived = 0
            """, (matter_id, app, app, url, url, title, title))

            existing = cursor.fetchone()

            if existing:
                # Reinforce existing pattern
                pattern_id, match_count, confidence = existing
                new_count = match_count + 1
                # Increase confidence slightly, max 1.0
                new_confidence = min(1.0, confidence + 0.05)

                cursor.execute("""
                    UPDATE categorization_patterns
                    SET match_count = ?, confidence_score = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_count, new_confidence, now, pattern_id))
                conn.commit()
                logging.info(f"Reinforced pattern {pattern_id}: count={new_count}, confidence={new_confidence:.2f}")
                return pattern_id
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO categorization_patterns
                    (matter_id, app_pattern, url_pattern, title_pattern, confidence_score, last_used_at)
                    VALUES (?, ?, ?, ?, 1.0, ?)
                """, (matter_id, app, url, title, now))
                conn.commit()
                pattern_id = cursor.lastrowid
                logging.info(f"Created new pattern {pattern_id} for matter {matter_id}")
                return pattern_id

    def record_correction_with_contradiction(
        self,
        correct_matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction that may contradict existing patterns.

        This is the primary method for handling user corrections. It:
        1. Finds any existing patterns that match these attributes
        2. Decreases confidence of patterns pointing to OTHER matters
        3. Creates/reinforces pattern for the correct matter

        Args:
            correct_matter_id: The matter user selected as correct
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or reinforced pattern
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Find existing patterns that match these attributes but point elsewhere
            contradicting_patterns = []
            if app:
                cursor.execute("""
                    SELECT id, confidence_score, correction_count
                    FROM categorization_patterns
                    WHERE app_pattern = ? AND matter_id != ? AND is_archived = 0
                """, (app, correct_matter_id))
                contradicting_patterns.extend(cursor.fetchall())

            # Decrease confidence of contradicting patterns
            for pattern_id, confidence, corrections in contradicting_patterns:
                new_confidence = max(0.1, confidence - 0.1)  # Min 0.1
                new_corrections = corrections + 1
                cursor.execute("""
                    UPDATE categorization_patterns
                    SET confidence_score = ?, correction_count = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_confidence, new_corrections, now, pattern_id))
                logging.info(f"Decreased confidence of pattern {pattern_id} to {new_confidence:.2f}")

            conn.commit()

        # Now record the correct pattern (will create or reinforce)
        return self.record_correction(correct_matter_id, app, url, title)

    def archive_stale_patterns(self, days: int = 90) -> int:
        """
        Archive patterns that haven't been used in the specified number of days.

        Archived patterns are excluded from matching but retained for analysis.

        Args:
            days: Number of days of inactivity before archiving (default: 90)

        Returns:
            Number of patterns archived
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                UPDATE categorization_patterns
                SET is_archived = 1
                WHERE is_archived = 0
                AND last_used_at < ?
            """, (cutoff_date,))

            archived = cursor.rowcount
            conn.commit()

            if archived > 0:
                logging.info(f"Archived {archived} stale patterns (unused for {days}+ days)")

            return archived

    @staticmethod
    def _dict_factory(cursor, row):
        """Convert SQLite row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
