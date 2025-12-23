"""Test database schema for clients and matters tables."""
import tempfile
from pathlib import Path
import sys
import pytest
import sqlite3

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


@pytest.fixture
def temp_db():
    """Create a temporary database instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db


@pytest.fixture
def db_path(temp_db):
    """Get the database path from temp_db."""
    return temp_db.db_path


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


def test_events_table_has_client_column(db_connection):
    """Verify events table has client column after migration."""
    cursor = db_connection.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'client' in columns


def test_events_table_has_matter_column(db_connection):
    """Verify events table has matter column after migration."""
    cursor = db_connection.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cursor.fetchall()}
    assert 'matter' in columns


def test_events_client_matter_columns_nullable(db_connection):
    """Verify client/matter columns allow NULL (user assigns later)."""
    # Insert event without client/matter
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO events (title, app, timestamp, state)
        VALUES ('Test', 'test.exe', datetime('now'), 'Active')
    """)
    db_connection.commit()

    # Verify NULL values accepted
    cursor.execute("SELECT client, matter FROM events WHERE title='Test'")
    row = cursor.fetchone()
    assert row[0] is None  # client is NULL
    assert row[1] is None  # matter is NULL


def test_migrate_screenshots_analysis_columns(db_path, temp_db):
    """Test that analysis columns are added to screenshots table."""
    # First verify columns don't exist
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

    # Run migration
    temp_db._migrate_screenshots_table()

    # Verify columns now exist
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [row[1] for row in cursor.fetchall()]

    assert 'analysis_data' in columns
    assert 'analysis_status' in columns
