"""Test AI learning database for categorization patterns."""
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
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


def test_record_user_correction():
    """Test recording a user correction creates appropriate pattern."""
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

        # User corrects: activity was misclassified, should be matter 2024-001
        pattern_id = db.record_correction(
            matter_id=matter_id,
            app="WINWORD.EXE",
            url=None,
            title="Smith Contract Draft.docx - Word"
        )

        assert pattern_id > 0

        # Pattern should now match similar activities
        matches = db.find_matching_patterns(app="WINWORD.EXE")
        assert len(matches) == 1
        assert matches[0]['matter_id'] == matter_id


def test_duplicate_correction_increases_confidence():
    """Test that repeated corrections increase pattern confidence."""
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

        # First correction
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)
        initial_confidence = patterns[0]['confidence_score']
        initial_count = patterns[0]['match_count']

        # Same correction again - should reinforce pattern
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)

        assert patterns[0]['match_count'] > initial_count
        assert patterns[0]['confidence_score'] >= initial_confidence


def test_contradicting_correction_decreases_confidence():
    """Test that contradicting corrections decrease old pattern confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matters first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Matter A'))
        matter_a = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Matter B'))
        matter_b = cursor.lastrowid
        conn.commit()
        conn.close()

        # Initial pattern: WINWORD.EXE -> Matter A
        db.insert_pattern(matter_a, app_pattern="WINWORD.EXE", confidence_score=0.9)

        # User correction: same app but different matter
        db.record_correction_with_contradiction(
            correct_matter_id=matter_b,
            app="WINWORD.EXE"
        )

        # Old pattern confidence should decrease
        patterns_a = db.get_patterns_for_matter(matter_a)
        assert patterns_a[0]['confidence_score'] < 0.9
        assert patterns_a[0]['correction_count'] > 0

        # New pattern for matter B should exist
        patterns_b = db.get_patterns_for_matter(matter_b)
        assert len(patterns_b) == 1


def test_archive_stale_patterns():
    """Test archiving patterns not used in 90 days."""
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

        # Insert pattern with old last_used_at
        db.insert_pattern(matter_id, app_pattern="old_app.exe")

        # Manually set last_used_at to 100 days ago
        conn = sqlite3.connect(db_path)
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        conn.execute("UPDATE categorization_patterns SET last_used_at = ?", (old_date,))
        conn.commit()
        conn.close()

        # Run expiration
        archived_count = db.archive_stale_patterns(days=90)

        assert archived_count == 1

        # Pattern should not appear in normal queries
        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 0

        # But should appear if including archived
        patterns = db.get_patterns_for_matter(matter_id, include_archived=True)
        assert len(patterns) == 1
        assert patterns[0]['is_archived'] == 1


def test_export_patterns_for_llm():
    """Test exporting patterns in LLM-friendly JSON format."""
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

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE", confidence_score=0.95)
        db.insert_pattern(matter_id, url_pattern="*canlii.org*", confidence_score=0.8)

        # Export patterns
        patterns_json = db.export_patterns_json()
        patterns = json.loads(patterns_json)

        assert 'patterns' in patterns
        assert len(patterns['patterns']) == 2
        assert any(p['app_pattern'] == 'WINWORD.EXE' for p in patterns['patterns'])


def test_get_all_active_patterns():
    """Test retrieving all active patterns for export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matters first (using direct SQL due to schema mismatch bug)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Matter A'))
        matter_a = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)', (client_id, 'Matter B'))
        matter_b = cursor.lastrowid
        conn.commit()
        conn.close()

        db.insert_pattern(matter_a, app_pattern="app1.exe")
        db.insert_pattern(matter_b, app_pattern="app2.exe")

        all_patterns = db.get_all_patterns()
        assert len(all_patterns) == 2


if __name__ == "__main__":
    test_categorization_patterns_table_exists()
    test_categorization_patterns_table_schema()
    print("All tests passed!")
