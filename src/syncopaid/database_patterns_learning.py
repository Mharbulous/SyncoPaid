"""
Database operations for pattern learning from user corrections.

Handles recording user corrections when they change AI categorization suggestions,
including reinforcing correct patterns and decreasing confidence of contradicting ones.
"""

import logging
from typing import Optional
from datetime import datetime


class PatternsLearningMixin:
    """
    Mixin providing pattern learning operations from user corrections.

    Requires _get_connection() method from ConnectionMixin.
    """

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
