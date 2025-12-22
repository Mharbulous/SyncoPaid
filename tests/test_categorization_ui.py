import pytest
import tempfile
from pathlib import Path
from syncopaid.database import Database


def test_query_screenshots_by_timestamp():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Insert test screenshots
        db.insert_screenshot('2025-12-16T10:00:00', 'path1.png', 'app1', 'title1', 'hash1')
        db.insert_screenshot('2025-12-16T10:05:00', 'path2.png', 'app1', 'title2', 'hash2')

        from syncopaid.categorization_ui import query_screenshots_for_activity
        results = query_screenshots_for_activity(db, '2025-12-16T10:00:00', '2025-12-16T10:10:00')

        assert len(results) == 2
        assert results[0]['file_path'] == 'path1.png'
        assert results[1]['file_path'] == 'path2.png'
