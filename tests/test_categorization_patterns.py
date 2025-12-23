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


def test_insert_pattern():
    """Test inserting a new categorization pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Contract review'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Insert pattern
        pattern_id = db.insert_pattern(
            matter_id=matter_id,
            app_pattern="WINWORD.EXE",
            title_pattern="Contract*"
        )
        assert pattern_id > 0


def test_get_patterns_for_matter():
    """Test retrieving patterns for a specific matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Contract review'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE")
        db.insert_pattern(matter_id, url_pattern="*canlii.org*")

        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 2


def test_find_matching_patterns():
    """Test finding patterns that match activity attributes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Contract review'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE", confidence_score=0.9)

        # Should match
        matches = db.find_matching_patterns(app="WINWORD.EXE")
        assert len(matches) == 1
        assert matches[0]['matter_id'] == matter_id

        # Should not match
        no_matches = db.find_matching_patterns(app="chrome.exe")
        assert len(no_matches) == 0


def test_delete_pattern():
    """Test deleting a pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Test matter'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        pattern_id = db.insert_pattern(matter_id, app_pattern="test.exe")
        db.delete_pattern(pattern_id)

        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 0


if __name__ == "__main__":
    test_categorization_patterns_table_exists()
    test_categorization_patterns_table_schema()
    print("All tests passed!")
