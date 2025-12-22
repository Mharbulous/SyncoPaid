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


def test_add_keyword_to_matter():
    """Test adding a keyword to a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first using direct SQL (schema API mismatch)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)',
                      (client_id, 'Test Matter'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Add keyword
        keyword_id = db.add_matter_keyword(matter_id, "contract", source="ai", confidence=0.95)
        assert keyword_id > 0


def test_get_matter_keywords():
    """Test retrieving keywords for a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter using direct SQL
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)',
                      (client_id, 'Test Matter'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        db.add_matter_keyword(matter_id, "contract", source="ai", confidence=0.95)
        db.add_matter_keyword(matter_id, "litigation", source="ai", confidence=0.87)

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 2
        assert any(k['keyword'] == 'contract' for k in keywords)
        assert any(k['keyword'] == 'litigation' for k in keywords)


def test_delete_matter_keyword():
    """Test removing a keyword from a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter using direct SQL
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)',
                      (client_id, 'Test Matter'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        keyword_id = db.add_matter_keyword(matter_id, "obsolete", source="ai")
        db.delete_matter_keyword(keyword_id)

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 0


def test_update_matter_keywords_batch():
    """Test replacing all keywords for a matter (AI update pattern)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter using direct SQL
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)',
                      (client_id, 'Test Matter'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Initial keywords
        db.add_matter_keyword(matter_id, "old_keyword", source="ai")

        # AI updates with new analysis
        new_keywords = [
            {"keyword": "contract", "confidence": 0.95},
            {"keyword": "smith_v_jones", "confidence": 0.88}
        ]
        db.update_matter_keywords(matter_id, new_keywords, source="ai")

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 2
        assert not any(k['keyword'] == 'old_keyword' for k in keywords)
        assert any(k['keyword'] == 'contract' for k in keywords)


if __name__ == "__main__":
    test_matter_keywords_table_exists()
    test_matter_keywords_table_schema()
    print("All tests passed!")
