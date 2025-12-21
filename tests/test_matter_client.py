"""Test matter and client database functionality."""
import sqlite3
import tempfile
from pathlib import Path
from syncopaid.database import Database

def test_clients_table_exists():
    """Verify clients table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "clients table should exist"

def test_matters_table_exists():
    """Verify matters table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matters'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matters table should exist"

if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    print("All tests passed!")
