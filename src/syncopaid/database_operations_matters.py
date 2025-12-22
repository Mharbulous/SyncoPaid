"""
Database CRUD operations for matters.

Provides matter management operations.
"""

from typing import List, Dict, Optional


class MatterOperationsMixin:
    """
    Mixin providing matter-related database CRUD operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def insert_matter(self, matter_number: str, client_id: Optional[int] = None,
                      description: Optional[str] = None, status: str = 'active') -> int:
        """
        Insert a new matter into the database.

        Args:
            matter_number: Unique matter number
            client_id: ID of the associated client (optional)
            description: Matter description (optional)
            status: Matter status (default: 'active')

        Returns:
            The ID of the inserted matter
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matters (matter_number, client_id, description, status)
                VALUES (?, ?, ?, ?)
            """, (matter_number, client_id, description, status))
            return cursor.lastrowid

    def get_matters(self, status: str = 'active') -> List[Dict]:
        """
        Get matters with optional status filtering.

        Args:
            status: Filter by status ('active', 'archived', 'all')

        Returns:
            List of matter dictionaries with client names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status == 'all':
                cursor.execute("""
                    SELECT m.*, c.display_name as client_name FROM matters m
                    LEFT JOIN clients c ON m.client_id = c.id
                    ORDER BY m.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT m.*, c.display_name as client_name FROM matters m
                    LEFT JOIN clients c ON m.client_id = c.id
                    WHERE m.status = ? ORDER BY m.created_at DESC
                """, (status,))
            return [dict(row) for row in cursor.fetchall()]

    def update_matter(self, matter_id: int, matter_number: str,
                      client_id: Optional[int] = None, description: Optional[str] = None):
        """
        Update an existing matter.

        Args:
            matter_id: ID of the matter to update
            matter_number: New matter number
            client_id: New client ID (optional)
            description: New description (optional)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matters SET matter_number = ?, client_id = ?, description = ?,
                updated_at = datetime('now') WHERE id = ?
            """, (matter_number, client_id, description, matter_id))

    def update_matter_status(self, matter_id: int, status: str):
        """
        Update the status of a matter.

        Args:
            matter_id: ID of the matter to update
            status: New status (e.g., 'active', 'archived')
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matters SET status = ?, updated_at = datetime('now') WHERE id = ?
            """, (status, matter_id))
