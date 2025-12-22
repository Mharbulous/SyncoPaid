"""Test matter keyword analyzer service."""
import tempfile
from pathlib import Path
import sys
import sqlite3
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syncopaid.database import Database
from syncopaid.keyword_analyzer import MatterKeywordAnalyzer


def test_analyze_matter_keywords():
    """Test analyzing and storing keywords for a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter using direct SQL (schema API mismatch)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clients (display_name) VALUES (?)', ('Test Client',))
        client_id = cursor.lastrowid
        cursor.execute('INSERT INTO matters (client_id, display_name) VALUES (?, ?)',
                      (client_id, 'Smith v. Johnson'))
        matter_id = cursor.lastrowid
        conn.commit()
        conn.close()

        analyzer = MatterKeywordAnalyzer(db)
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Smith v. Johnson - Contract Draft.docx",
            "Smith v. Johnson case law research",
            "Smith v. Johnson - Motion to Dismiss",
        ])

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) > 0

        keyword_texts = [k['keyword'] for k in keywords]
        assert 'smith' in keyword_texts
        assert 'johnson' in keyword_texts


def test_analyze_matter_updates_existing():
    """Test that re-analysis updates keywords, not duplicates."""
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

        analyzer = MatterKeywordAnalyzer(db)

        # First analysis
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Contract review meeting",
            "Contract drafting session",
        ])
        initial_keywords = db.get_matter_keywords(matter_id)

        # Second analysis with different activities
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Litigation strategy discussion",
            "Court filing preparation",
        ])
        updated_keywords = db.get_matter_keywords(matter_id)

        # Should have replaced keywords, not accumulated
        keyword_texts = [k['keyword'] for k in updated_keywords]
        assert 'litigation' in keyword_texts or 'court' in keyword_texts
        # Old keywords should be gone
        assert 'contract' not in keyword_texts


if __name__ == "__main__":
    test_analyze_matter_keywords()
    test_analyze_matter_updates_existing()
    print("All tests passed!")
