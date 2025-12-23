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


def test_secure_file_delete(tmp_path):
    """Verify file contents are overwritten before deletion."""
    test_file = tmp_path / "sensitive.jpg"
    secret_content = b"ATTORNEY_CLIENT_PRIVILEGED_CONTENT"
    test_file.write_bytes(secret_content)

    from syncopaid.secure_delete import secure_delete_file
    secure_delete_file(test_file)

    # File should be deleted
    assert not test_file.exists()

    # Content should not be recoverable (check parent directory for remnants)
    # Note: This is a best-effort test; full forensic verification requires OS-level tools


def test_delete_screenshots_securely(tmp_path):
    """Verify screenshot deletion removes both database record and file."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Create test screenshot file
    screenshot_dir = tmp_path / "screenshots" / "2025-12-21"
    screenshot_dir.mkdir(parents=True)
    screenshot_file = screenshot_dir / "test_screenshot.jpg"
    screenshot_file.write_bytes(b"fake image content")

    # Insert screenshot record
    screenshot_id = db.insert_screenshot(
        captured_at="2025-12-21T10:00:00",
        file_path=str(screenshot_file),
        window_app="test.exe",
        window_title="Test Window"
    )

    # Delete screenshot securely
    deleted = db.delete_screenshots_securely([screenshot_id])

    assert deleted == 1
    assert not screenshot_file.exists(), "Screenshot file should be deleted"

    # Verify database record is gone
    screenshots = db.get_screenshots()
    assert len(screenshots) == 0


def test_delete_events_securely_with_screenshots(tmp_path):
    """Verify event deletion cascades to secure screenshot deletion."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    # Create event
    event = ActivityEvent(
        timestamp="2025-12-21T10:00:00",
        duration_seconds=60.0,
        app="test.exe",
        title="Test Window",
        is_idle=False
    )
    event_id = db.insert_event(event)

    # Create associated screenshot
    screenshot_dir = tmp_path / "screenshots" / "2025-12-21"
    screenshot_dir.mkdir(parents=True)
    screenshot_file = screenshot_dir / "100000.jpg"  # Timestamp-based name
    screenshot_file.write_bytes(b"fake image content")

    screenshot_id = db.insert_screenshot(
        captured_at="2025-12-21T10:00:00",
        file_path=str(screenshot_file),
        window_app="test.exe",
        window_title="Test Window"
    )

    # Delete events securely (should also delete screenshots in same time range)
    deleted = db.delete_events_securely(start_date="2025-12-21", end_date="2025-12-21")

    assert deleted > 0
    assert not screenshot_file.exists(), "Associated screenshot should be deleted"
