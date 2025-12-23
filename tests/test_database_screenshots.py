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


def test_get_pending_analysis_screenshots(db_screenshots, sample_screenshot):
    """Test retrieving screenshots pending analysis."""
    # Insert multiple screenshots
    for i in range(5):
        db_screenshots.insert_screenshot(
            file_path=f'/screenshots/img_{i}.png',
            window_app='App',
            window_title=f'Window {i}',
            captured_at=datetime.now().isoformat()
        )

    # Get pending screenshots
    pending = db_screenshots.get_pending_analysis_screenshots(limit=10)

    assert len(pending) == 5
    assert all('id' in s for s in pending)
    assert all('file_path' in s for s in pending)


def test_get_pending_analysis_screenshots_excludes_completed(db_screenshots, sample_screenshot):
    """Test that completed screenshots are not returned."""
    # Insert screenshot and mark as completed
    screenshot_id = db_screenshots.insert_screenshot(
        file_path='/screenshots/completed.png',
        window_app='App',
        window_title='Window',
        captured_at=datetime.now().isoformat()
    )
    db_screenshots.update_screenshot_analysis(
        screenshot_id=screenshot_id,
        analysis_data='{"confidence": 1.0}',
        analysis_status='completed'
    )

    # Insert another pending screenshot
    db_screenshots.insert_screenshot(
        file_path='/screenshots/pending.png',
        window_app='App',
        window_title='Window 2',
        captured_at=datetime.now().isoformat()
    )

    pending = db_screenshots.get_pending_analysis_screenshots()

    assert len(pending) == 1
    assert pending[0]['file_path'] == '/screenshots/pending.png'


def test_get_pending_analysis_screenshots_respects_limit(db_screenshots):
    """Test limit parameter works correctly."""
    # Insert 10 screenshots
    for i in range(10):
        db_screenshots.insert_screenshot(
            file_path=f'/screenshots/img_{i}.png',
            window_app='App',
            window_title=f'Window {i}',
            captured_at=datetime.now().isoformat()
        )

    pending = db_screenshots.get_pending_analysis_screenshots(limit=3)

    assert len(pending) == 3


@pytest.fixture
def db_with_screenshots(db_screenshots):
    """Create database with 3 screenshots with NULL analysis_status."""
    for i in range(3):
        db_screenshots.insert_screenshot(
            file_path=f'/screenshots/img_{i}.png',
            window_app='App',
            window_title=f'Window {i}',
            captured_at=datetime.now().isoformat()
        )
    return db_screenshots


def test_get_pending_screenshot_count_returns_count(db_with_screenshots):
    """Test that get_pending_screenshot_count returns correct count."""
    # Arrange: db_with_screenshots fixture creates 3 screenshots with NULL analysis_status

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 3


def test_get_pending_screenshot_count_excludes_completed(db_with_screenshots):
    """Test that completed screenshots are not counted."""
    # Arrange: Update one screenshot to 'completed'
    with db_with_screenshots._get_connection() as conn:
        conn.execute(
            "UPDATE screenshots SET analysis_status = 'completed' WHERE id = 1"
        )

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 2
