"""Test AI learning database for categorization patterns."""
import sqlite3
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


def test_categorization_patterns_table_exists():
    """Verify categorization_patterns table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categorization_patterns'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "categorization_patterns table should exist"


def test_categorization_patterns_table_schema():
    """Verify categorization_patterns table has correct columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(categorization_patterns)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Required columns from acceptance criteria
        assert 'id' in columns
        assert 'matter_id' in columns
        assert 'app_pattern' in columns
        assert 'url_pattern' in columns
        assert 'title_pattern' in columns
        assert 'confidence_score' in columns
        assert 'created_at' in columns
        assert 'last_used_at' in columns


if __name__ == "__main__":
    test_categorization_patterns_table_exists()
    test_categorization_patterns_table_schema()
    print("All tests passed!")
