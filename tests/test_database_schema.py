"""Test database schema for clients and matters tables."""
import tempfile
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


@pytest.fixture
def db_connection():
    """Create a temporary database and return connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        with db._get_connection() as conn:
            yield conn


def test_clients_table_exists(db_connection):
    """Verify clients table is created with correct schema."""
    cursor = db_connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='clients'"
    )
    schema = cursor.fetchone()
    assert schema is not None
    assert 'display_name TEXT NOT NULL' in schema[0]
    assert 'folder_path TEXT' in schema[0]
    assert 'created_at TEXT' in schema[0]
    assert 'UNIQUE(display_name)' in schema[0]


def test_matters_table_exists(db_connection):
    """Verify matters table is created with correct schema."""
    cursor = db_connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='matters'"
    )
    schema = cursor.fetchone()
    assert schema is not None
    assert 'client_id INTEGER NOT NULL' in schema[0]
    assert 'display_name TEXT NOT NULL' in schema[0]
    assert 'FOREIGN KEY(client_id) REFERENCES clients(id)' in schema[0]
    assert 'UNIQUE(client_id, display_name)' in schema[0]
