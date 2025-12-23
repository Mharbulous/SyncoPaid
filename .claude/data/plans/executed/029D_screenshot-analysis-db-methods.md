# 029D: Screenshot Analysis Database Methods
Story ID: 15.1

## Task
Add database methods for storing and querying screenshot analysis results.

## Context
This is the fourth sub-plan of 029 (Automatic Screenshot Analysis). Implements database operations for updating screenshots with analysis data and retrieving pending screenshots.

## Scope
- Add `update_screenshot_analysis()` method to database
- Add `get_pending_analysis_screenshots()` method
- Tests for both methods

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database_screenshots.py` | Add analysis methods |
| `tests/test_database_screenshots.py` | Add method tests |

## TDD Tasks

### Task 1: Add update_screenshot_analysis method

**Test first:**
```python
# tests/test_database_screenshots.py - Add to existing file
import json


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
```

**Implementation:**
```python
# src/syncopaid/database_screenshots.py - Add method
from typing import List, Dict, Optional


def update_screenshot_analysis(
    self,
    screenshot_id: int,
    analysis_data: Optional[str],
    analysis_status: str = 'completed'
) -> None:
    """
    Update screenshot with analysis results.

    Args:
        screenshot_id: ID of screenshot record
        analysis_data: JSON string of analysis results (or None if failed)
        analysis_status: 'pending', 'completed', or 'failed'
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE screenshots
            SET analysis_data = ?, analysis_status = ?
            WHERE id = ?
        """, (analysis_data, analysis_status, screenshot_id))
        conn.commit()
```

### Task 2: Add get_pending_analysis_screenshots method

**Test first:**
```python
def test_get_pending_analysis_screenshots(db_screenshots, sample_screenshot):
    """Test retrieving screenshots pending analysis."""
    # Insert multiple screenshots
    for i in range(5):
        db_screenshots.insert_screenshot(
            file_path=f'/screenshots/img_{i}.png',
            window_app='App',
            window_title=f'Window {i}',
            captured_at=datetime.now()
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
        captured_at=datetime.now()
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
        captured_at=datetime.now()
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
            captured_at=datetime.now()
        )

    pending = db_screenshots.get_pending_analysis_screenshots(limit=3)

    assert len(pending) == 3
```

**Implementation:**
```python
# src/syncopaid/database_screenshots.py - Add method
def get_pending_analysis_screenshots(self, limit: int = 10) -> List[Dict]:
    """
    Get screenshots pending analysis.

    Args:
        limit: Maximum number of screenshots to return

    Returns:
        List of screenshot records with id, file_path, window_app, window_title
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, window_app, window_title
            FROM screenshots
            WHERE analysis_status = 'pending' OR analysis_status IS NULL
            ORDER BY captured_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_database_screenshots.py -v -k "analysis"
python -m syncopaid.database
```

## Notes
- Methods support the async analysis workflow
- Pending includes both NULL and 'pending' status for backwards compatibility
- Results ordered by most recent first (captured_at DESC)
