"""Test database functionality for transitions."""
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database
from syncopaid.tracker import ActivityEvent


def test_transitions_table_exists():
    """Test transitions table exists in schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        with db._get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transitions'")
            assert cursor.fetchone() is not None, "transitions table should exist"


def test_insert_transition():
    """Test inserting a transition event."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        transition_id = db.insert_transition(
            timestamp="2025-12-17T10:30:00",
            transition_type="idle_return",
            context={"idle_seconds": 320},
            user_response=None
        )
        assert transition_id > 0


def test_metadata_column_exists():
    """Test that metadata column exists in events table."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        with db._get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(events)")
            columns = {row[1] for row in cursor.fetchall()}
            assert 'metadata' in columns, "events table should have metadata column"


def test_insert_event_with_metadata():
    """Test inserting an event with metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        metadata = {"email_subject": "Re: Smith Case", "sender": "client@example.com"}
        event = ActivityEvent(
            timestamp="2025-12-17T10:30:00",
            duration_seconds=60.0,
            app="OUTLOOK.EXE",
            title="Re: Smith Case - Outlook",
            is_idle=False,
            metadata=metadata
        )
        event_id = db.insert_event(event)
        assert event_id > 0


def test_get_events_with_metadata():
    """Test retrieving events with metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Insert event with metadata
        metadata = {"folder_path": "C:\\Cases\\Smith_v_Jones"}
        event = ActivityEvent(
            timestamp="2025-12-17T10:30:00",
            duration_seconds=60.0,
            app="explorer.exe",
            title="Smith_v_Jones",
            is_idle=False,
            metadata=metadata
        )
        db.insert_event(event)

        # Retrieve events
        events = db.get_events()
        assert len(events) > 0
        event = events[0]
        assert 'metadata' in event
        assert event['metadata'] == metadata
