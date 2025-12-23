"""Test database screenshot operations."""
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


@pytest.fixture
def db_screenshots():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db


@pytest.fixture
def sample_screenshot():
    """Sample screenshot data for testing."""
    return {
        'file_path': '/screenshots/2025-12-23/screenshot_001.png',
        'window_app': 'TestApp',
        'window_title': 'Test Window',
        'captured_at': datetime.now().isoformat()
    }


def test_update_screenshot_analysis(db_screenshots, sample_screenshot):
    """Test updating screenshot with analysis results."""
    # Insert a screenshot first
    screenshot_id = db_screenshots.insert_screenshot(
        file_path=sample_screenshot['file_path'],
        window_app=sample_screenshot['window_app'],
        window_title=sample_screenshot['window_title'],
        captured_at=sample_screenshot['captured_at']
    )

    # Update with analysis
    analysis_json = json.dumps({
        'application': 'Word',
        'document_name': 'Brief.docx',
        'confidence': 0.9
    })
    db_screenshots.update_screenshot_analysis(
        screenshot_id=screenshot_id,
        analysis_data=analysis_json,
        analysis_status='completed'
    )

    # Verify update
    with db_screenshots._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT analysis_data, analysis_status FROM screenshots WHERE id = ?",
            (screenshot_id,)
        )
        row = cursor.fetchone()

    assert row['analysis_data'] == analysis_json
    assert row['analysis_status'] == 'completed'


def test_update_screenshot_analysis_failed_status(db_screenshots, sample_screenshot):
    """Test updating screenshot with failed analysis status."""
    screenshot_id = db_screenshots.insert_screenshot(
        file_path=sample_screenshot['file_path'],
        window_app=sample_screenshot['window_app'],
        window_title=sample_screenshot['window_title'],
        captured_at=sample_screenshot['captured_at']
    )

    db_screenshots.update_screenshot_analysis(
        screenshot_id=screenshot_id,
        analysis_data=None,
        analysis_status='failed'
    )

    with db_screenshots._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT analysis_status FROM screenshots WHERE id = ?",
            (screenshot_id,)
        )
        row = cursor.fetchone()

    assert row['analysis_status'] == 'failed'
