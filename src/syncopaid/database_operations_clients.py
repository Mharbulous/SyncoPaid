"""
Database CRUD operations for clients.

Provides client management operations.
"""

from typing import List, Dict, Optional


class ClientOperationsMixin:
    """
    Mixin providing client-related database CRUD operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def insert_client(self, name: str, notes: Optional[str] = None) -> int:
        """
        Insert a new client into the database.

        Args:
            name: Client name
            notes: Optional notes about the client

        Returns:
            The ID of the inserted client
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clients (display_name) VALUES (?)", (name,))
            return cursor.lastrowid

    def get_clients(self) -> List[Dict]:
        """
        Get all clients ordered by name.

        Returns:
            List of client dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY display_name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def update_client(self, client_id: int, name: str, notes: Optional[str] = None):
        """
        Update an existing client.

        Args:
            client_id: ID of the client to update
            name: New client name
            notes: New notes (optional)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE clients SET display_name = ? WHERE id = ?",
                          (name, client_id))

    def delete_client(self, client_id: int):
        """
        Delete a client from the database.

        Args:
            client_id: ID of the client to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
