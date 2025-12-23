"""
Database operations for screenshot management.

Provides methods for inserting, updating, and querying screenshot records
in the SQLite database.
"""

import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager


class ScreenshotDatabaseMixin:
    """
    Mixin class providing screenshot database operations.

    Must be mixed with a class that provides:
    - self.db_path: Path to SQLite database
    - self._get_connection(): Context manager for database connections
    """

    def insert_screenshot(
        self,
        captured_at: str,
        file_path: str,
        window_app: Optional[str] = None,
        window_title: Optional[str] = None,
        dhash: Optional[str] = None
    ) -> int:
        """
        Insert a screenshot record into the database.

        Args:
            captured_at: ISO timestamp when screenshot was captured
            file_path: Path to the saved screenshot file
            window_app: Application name when screenshot was taken
            window_title: Window title when screenshot was taken
            dhash: Perceptual hash (dHash) of the screenshot for deduplication

        Returns:
            The ID of the inserted screenshot record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO screenshots (captured_at, file_path, window_app, window_title, dhash)
                VALUES (?, ?, ?, ?, ?)
            """, (captured_at, file_path, window_app, window_title, dhash))

            return cursor.lastrowid

    def update_screenshot(
        self,
        screenshot_id: int,
        file_path: Optional[str] = None,
        dhash: Optional[str] = None
    ):
        """
        Update an existing screenshot record (used when overwriting).

        Args:
            screenshot_id: ID of the screenshot record to update
            file_path: New file path (if changed)
            dhash: New perceptual hash (if changed)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if file_path is not None:
                updates.append("file_path = ?")
                params.append(file_path)

            if dhash is not None:
                updates.append("dhash = ?")
                params.append(dhash)

            if not updates:
                return

            params.append(screenshot_id)
            query = f"UPDATE screenshots SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

    def get_screenshots(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query screenshots with optional filtering.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            limit: Maximum number of screenshots to return

        Returns:
            List of screenshot dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = "SELECT * FROM screenshots WHERE 1=1"
            params = []

            if start_date:
                query += " AND captured_at >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND captured_at < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            query += " ORDER BY captured_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            # Convert rows to dictionaries
            screenshots = []
            for row in cursor.fetchall():
                screenshots.append({
                    'id': row['id'],
                    'captured_at': row['captured_at'],
                    'file_path': row['file_path'],
                    'window_app': row['window_app'],
                    'window_title': row['window_title'],
                    'dhash': row['dhash']
                })

            return screenshots

    def get_latest_screenshot(self) -> Optional[Dict]:
        """
        Get the most recent screenshot record.

        Returns:
            Screenshot dictionary or None if no screenshots exist
        """
        screenshots = self.get_screenshots(limit=1)
        return screenshots[0] if screenshots else None

    def delete_screenshots_securely(self, screenshot_ids: List[int]) -> int:
        """
        Securely delete screenshots by ID, removing both database records and files.

        Files are overwritten with zeros before deletion to prevent forensic recovery.

        Args:
            screenshot_ids: List of screenshot IDs to delete

        Returns:
            Number of screenshots deleted
        """
        from .secure_delete import secure_delete_file
        from pathlib import Path

        if not screenshot_ids:
            return 0

        deleted_count = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get file paths before deletion
            placeholders = ','.join('?' * len(screenshot_ids))
            cursor.execute(
                f"SELECT id, file_path FROM screenshots WHERE id IN ({placeholders})",
                screenshot_ids
            )
            screenshots = cursor.fetchall()

            # Securely delete each file
            for row in screenshots:
                file_path = Path(row['file_path'])
                secure_delete_file(file_path)

            # Delete database records
            cursor.execute(
                f"DELETE FROM screenshots WHERE id IN ({placeholders})",
                screenshot_ids
            )
            deleted_count = cursor.rowcount

        logging.info(f"Securely deleted {deleted_count} screenshots")
        return deleted_count

    def update_screenshot_analysis(
        self,
        screenshot_id: int,
        analysis_data: Optional[str],
        analysis_status: str = 'completed'
    ) -> None:
        """
        Update screenshot with analysis results.

        Args:
            screenshot_id: ID of screenshot record
            analysis_data: JSON string of analysis results (or None if failed)
            analysis_status: 'pending', 'completed', or 'failed'
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots
                SET analysis_data = ?, analysis_status = ?
                WHERE id = ?
            """, (analysis_data, analysis_status, screenshot_id))
            conn.commit()
