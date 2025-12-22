"""Test matter keywords database functionality."""
import sqlite3
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


def test_matter_keywords_table_exists():
    """Verify matter_keywords table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matter_keywords'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matter_keywords table should exist"


def test_matter_keywords_table_schema():
    """Verify matter_keywords table has correct columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(matter_keywords)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'matter_id' in columns
        assert 'keyword' in columns
        assert 'source' in columns  # 'ai' or 'manual' (future)
        assert 'confidence' in columns
        assert 'created_at' in columns


if __name__ == "__main__":
    test_matter_keywords_table_exists()
    test_matter_keywords_table_schema()
    print("All tests passed!")
