"""
Database operations for transition events.

Provides transition tracking for timing patterns.
"""

import json
from typing import Optional


class TransitionOperationsMixin:
    """
    Mixin providing transition-related database operations.

    Requires _get_connection() method from ConnectionMixin.
    """

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
