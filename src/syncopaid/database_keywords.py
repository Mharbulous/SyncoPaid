"""
Database operations for AI-managed matter keywords.

Keywords are extracted and updated by AI to improve activity categorization.
Users view keywords read-only; AI has full control over keyword maintenance.
"""

import logging
from typing import List, Dict, Optional


class KeywordsDatabaseMixin:
    """
    Mixin providing matter keyword operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def add_matter_keyword(
        self,
        matter_id: int,
        keyword: str,
        source: str = "ai",
        confidence: float = 1.0
    ) -> int:
        """
        Add a keyword to a matter.

        Args:
            matter_id: ID of the matter
            keyword: The keyword text (lowercase, normalized)
            source: Origin of keyword ('ai' for AI-extracted)
            confidence: AI confidence score (0.0-1.0)

        Returns:
            ID of the inserted keyword record
        """
        keyword = keyword.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO matter_keywords
                (matter_id, keyword, source, confidence)
                VALUES (?, ?, ?, ?)
            """, (matter_id, keyword, source, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_matter_keywords(self, matter_id: int) -> List[Dict]:
        """
        Get all keywords for a matter.

        Args:
            matter_id: ID of the matter

        Returns:
            List of keyword dicts with id, keyword, source, confidence, created_at
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, keyword, source, confidence, created_at
                FROM matter_keywords
                WHERE matter_id = ?
                ORDER BY confidence DESC, keyword ASC
            """, (matter_id,))
            return cursor.fetchall()

    def delete_matter_keyword(self, keyword_id: int) -> bool:
        """
        Delete a keyword by ID.

        Args:
            keyword_id: ID of the keyword record

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM matter_keywords WHERE id = ?", (keyword_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_matter_keywords(
        self,
        matter_id: int,
        keywords: List[Dict],
        source: str = "ai"
    ) -> int:
        """
        Replace all keywords for a matter with new AI-extracted keywords.

        This is the primary method for AI keyword updates - removes old keywords
        and inserts the new set atomically.

        Args:
            matter_id: ID of the matter
            keywords: List of dicts with 'keyword' and optional 'confidence'
            source: Origin of keywords ('ai' for AI-extracted)

        Returns:
            Number of keywords inserted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Remove existing keywords from this source
            cursor.execute(
                "DELETE FROM matter_keywords WHERE matter_id = ? AND source = ?",
                (matter_id, source)
            )

            # Insert new keywords
            count = 0
            for kw in keywords:
                keyword = kw.get('keyword', '').lower().strip()
                if not keyword:
                    continue
                confidence = float(kw.get('confidence', 1.0))
                cursor.execute("""
                    INSERT OR REPLACE INTO matter_keywords
                    (matter_id, keyword, source, confidence)
                    VALUES (?, ?, ?, ?)
                """, (matter_id, keyword, source, confidence))
                count += 1

            conn.commit()
            logging.info(f"Updated {count} keywords for matter {matter_id}")
            return count

    def find_matters_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Find all matters that have a specific keyword.

        Args:
            keyword: Keyword to search for (case-insensitive)

        Returns:
            List of matter dicts with id, matter_number, description
        """
        keyword = keyword.lower().strip()
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT m.id, m.display_name, mk.confidence
                FROM matters m
                INNER JOIN matter_keywords mk ON m.id = mk.matter_id
                WHERE mk.keyword = ?
                ORDER BY mk.confidence DESC
            """, (keyword,))
            return cursor.fetchall()

    @staticmethod
    def _dict_factory(cursor, row):
        """Convert SQLite row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
