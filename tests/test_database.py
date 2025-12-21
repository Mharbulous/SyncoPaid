"""Test database functionality for transitions."""
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


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
