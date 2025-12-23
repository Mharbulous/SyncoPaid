"""
Tests for SQLite secure_delete pragma functionality.

Verifies that deleted data is overwritten and cannot be recovered.
"""

import pytest
from syncopaid.database import Database
from syncopaid.tracker_state import ActivityEvent


def test_secure_delete_pragma_enabled(tmp_path):
    """Verify secure_delete=ON is set on database connections."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    with db._get_connection() as conn:
        cursor = conn.execute("PRAGMA secure_delete")
        result = cursor.fetchone()[0]
        assert result == 1, "secure_delete pragma should be enabled (1)"
