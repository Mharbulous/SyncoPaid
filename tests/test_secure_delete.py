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


def test_secure_delete_overwrites_data(tmp_path):
    """Verify deleted data is overwritten, not just marked as deleted."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Insert event with distinctive string
    secret_marker = "CONFIDENTIAL_CLIENT_DATA_12345"
    event = ActivityEvent(
        timestamp="2025-12-21T10:00:00",
        duration_seconds=60.0,
        app="test.exe",
        title=secret_marker,
        is_idle=False
    )
    event_id = db.insert_event(event)

    # Force write to disk
    with db._get_connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Delete the event
    db.delete_events_by_ids([event_id])

    # Force write to disk again
    with db._get_connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Read raw database file and search for marker
    raw_content = db_path.read_bytes()
    assert secret_marker.encode() not in raw_content, \
        "Deleted data should not be recoverable from database file"
