"""
Database CRUD operations for activity events.

Provides:
- Insert single or batch events
- Query events with filtering
- Delete events by date range or IDs
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .tracker import ActivityEvent


class OperationsMixin:
    """
    Mixin providing database CRUD operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def insert_event(self, event: ActivityEvent) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')
            metadata = getattr(event, 'metadata', None)

            # Serialize metadata to JSON if present
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                1 if event.is_idle else 0,
                state,
                metadata_json
            ))

            return cursor.lastrowid

    def insert_events_batch(self, events: List[ActivityEvent]) -> int:
        """
        Insert multiple events in a single transaction (more efficient).

        Args:
            events: List of ActivityEvent objects

        Returns:
            Number of events inserted
        """
        if not events:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url, 1 if e.is_idle else 0, getattr(e, 'state', 'Active'),
                 json.dumps(getattr(e, 'metadata', None)) if getattr(e, 'metadata', None) else None)
                for e in events
            ])

            return len(events)

    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_idle: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query events with optional filtering.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            include_idle: Whether to include idle events (default True)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND timestamp < ?"
                # Add one day to make end_date inclusive
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            if not include_idle:
                query += " AND is_idle = 0"

            query += " ORDER BY timestamp ASC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            # Convert rows to dictionaries
            return self._rows_to_dicts(cursor.fetchall())

    def delete_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        Delete events within a date range.

        CAUTION: This permanently removes data. Use carefully.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)

        Returns:
            Number of events deleted
        """
        if not start_date and not end_date:
            raise ValueError("Must specify at least start_date or end_date")

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build delete query
            query = "DELETE FROM events WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND timestamp < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            cursor.execute(query, params)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events from database")
            return deleted_count

    def delete_events_by_ids(self, event_ids: List[int]) -> int:
        """
        Delete specific events by their IDs.

        Args:
            event_ids: List of event IDs to delete

        Returns:
            Number of events deleted
        """
        if not event_ids:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use parameterized query with placeholders
            placeholders = ','.join('?' * len(event_ids))
            query = f"DELETE FROM events WHERE id IN ({placeholders})"

            cursor.execute(query, event_ids)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events by ID from database")
            return deleted_count

    def _rows_to_dicts(self, rows) -> List[Dict]:
        """
        Convert database rows to dictionaries with backward compatibility.

        Args:
            rows: Database rows with row factory

        Returns:
            List of event dictionaries
        """
        events = []
        for row in rows:
            # Derive state from is_idle if column doesn't exist (backward compatibility)
            if 'state' in row.keys() and row['state']:
                state = row['state']
            else:
                state = 'Inactive' if row['is_idle'] else 'Active'

            # Deserialize metadata JSON if present
            metadata = None
            if 'metadata' in row.keys() and row['metadata']:
                metadata = json.loads(row['metadata'])

            events.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'duration_seconds': row['duration_seconds'],
                'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                'app': row['app'],
                'title': row['title'],
                'url': row['url'],
                'is_idle': bool(row['is_idle']),
                'state': state,
                'metadata': metadata
            })

        return events

    def insert_transition(self, timestamp: str, transition_type: str, context: dict = None, user_response: str = None) -> int:
        """
        Insert a transition event for tracking timing patterns.

        Args:
            timestamp: ISO timestamp of the transition
            transition_type: Type of transition (e.g., 'idle_return', 'inbox_browsing')
            context: Optional dict with transition context data
            user_response: Optional user response from prompt

        Returns:
            The ID of the inserted transition
        """
        context_json = json.dumps(context) if context else None

        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO transitions (timestamp, transition_type, context, user_response) VALUES (?, ?, ?, ?)",
                (timestamp, transition_type, context_json, user_response)
            )
            return cursor.lastrowid

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
            cursor.execute("INSERT INTO clients (name, notes) VALUES (?, ?)", (name, notes))
            return cursor.lastrowid

    def get_clients(self) -> List[Dict]:
        """
        Get all clients ordered by name.

        Returns:
            List of client dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY name ASC")
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
            cursor.execute("UPDATE clients SET name = ?, notes = ? WHERE id = ?",
                          (name, notes, client_id))

    def delete_client(self, client_id: int):
        """
        Delete a client from the database.

        Args:
            client_id: ID of the client to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))

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
                    SELECT m.*, c.name as client_name FROM matters m
                    LEFT JOIN clients c ON m.client_id = c.id
                    ORDER BY m.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT m.*, c.name as client_name FROM matters m
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
