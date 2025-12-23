# Handling Analysis Failures - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.5 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Gracefully handle screenshots that fail AI analysis by marking them for manual review, logging failure reasons, and providing a review interface.

**Approach:** Extend the screenshot database schema with failure tracking fields, update ScreenshotAnalyzer to return structured failure reasons, add database methods for querying failed screenshots, and extend the existing ScreenshotReviewDialog with a "Needs Review" filter.

**Tech Stack:** Python 3.11+, SQLite, tkinter for UI, existing screenshot_analyzer.py/database_screenshots.py infrastructure

---

## Story Context

**Title:** Handling Analysis Failures
**Description:** Gracefully handle screenshots that can't be analyzed

**Acceptance Criteria:**
- [ ] If AI can't analyze a screenshot, mark it as "needs manual review"
- [ ] Show screenshots that failed analysis in review interface
- [ ] Allow manual categorization of failed items
- [ ] Log reason for failure (e.g., "blank screen", "no text visible")
- [ ] Don't crash or hang on problematic images

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Screenshot analyzer exists (src/syncopaid/screenshot_analyzer.py)
- [ ] Screenshot review dialog exists (src/syncopaid/screenshot_review_dialog.py)

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_screenshot_analyzer.py` | Modify | Add failure reason tests |
| `src/syncopaid/screenshot_analyzer.py` | Modify | Add failure_reason to AnalysisResult |
| `tests/test_database_screenshots.py` | Modify | Add failure tracking tests |
| `src/syncopaid/database_schema_screenshots.py` | Modify | Add failure_reason column migration |
| `src/syncopaid/database_screenshots.py` | Modify | Add methods for failed screenshots |
| `tests/test_screenshot_review_dialog.py` | Modify | Add failed screenshots filter tests |
| `src/syncopaid/screenshot_review_dialog.py` | Modify | Add "Needs Review" filter tab |

## TDD Tasks

### Task 1: Add failure_reason field to AnalysisResult (~3 min)

**Files:**
- Modify: `src/syncopaid/screenshot_analyzer.py`
- Test: `tests/test_screenshot_analyzer.py`

**Context:** AnalysisResult is a dataclass returned by the analyzer. It needs a failure_reason field to explain why analysis failed (e.g., "blank_screen", "no_text_visible", "image_corrupted", "timeout").

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_analyzer.py - add new tests after existing tests

def test_analysis_result_has_failure_reason():
    """Test AnalysisResult includes failure_reason field."""
    result = AnalysisResult(failure_reason="blank_screen")

    assert result.failure_reason == "blank_screen"


def test_analysis_result_failure_reason_default_is_none():
    """Test failure_reason defaults to None (no failure)."""
    result = AnalysisResult()

    assert result.failure_reason is None


def test_analysis_result_failure_reason_serializes():
    """Test failure_reason is included in JSON serialization."""
    result = AnalysisResult(failure_reason="no_text_visible", confidence=0.1)

    json_str = result.to_json()
    restored = AnalysisResult.from_json(json_str)

    assert restored.failure_reason == "no_text_visible"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_analyzer.py::test_analysis_result_has_failure_reason -v
```
Expected output: `FAILED` (TypeError: AnalysisResult.__init__() got an unexpected keyword argument 'failure_reason')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot_analyzer.py - modify AnalysisResult dataclass (around line 11-21)
@dataclass
class AnalysisResult:
    """Result of screenshot analysis."""
    application: Optional[str] = None
    document_name: Optional[str] = None
    case_numbers: List[str] = field(default_factory=list)
    email_subject: Optional[str] = None
    webpage_title: Optional[str] = None
    visible_text: List[str] = field(default_factory=list)
    confidence: float = 0.0
    failure_reason: Optional[str] = None  # NEW: e.g., "blank_screen", "no_text_visible"

    def to_json(self) -> str:
        """Serialize to JSON for database storage."""
        return json.dumps({
            'application': self.application,
            'document_name': self.document_name,
            'case_numbers': self.case_numbers,
            'email_subject': self.email_subject,
            'webpage_title': self.webpage_title,
            'visible_text': self.visible_text,
            'confidence': self.confidence,
            'failure_reason': self.failure_reason  # NEW
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisResult':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(
            application=data.get('application'),
            document_name=data.get('document_name'),
            case_numbers=data.get('case_numbers', []),
            email_subject=data.get('email_subject'),
            webpage_title=data.get('webpage_title'),
            visible_text=data.get('visible_text', []),
            confidence=float(data.get('confidence', 0.0)),
            failure_reason=data.get('failure_reason')  # NEW
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_analyzer.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/screenshot_analyzer.py tests/test_screenshot_analyzer.py && git commit -m "feat(8.6.5): add failure_reason field to AnalysisResult"
```

---

### Task 2: Detect and classify analysis failures in analyzer (~5 min)

**Files:**
- Modify: `src/syncopaid/screenshot_analyzer.py`
- Test: `tests/test_screenshot_analyzer.py`

**Context:** The analyze() method should detect failure conditions and return appropriate failure_reason values. Common failures: blank screen (very low complexity), no extractable text, image corrupted, timeout.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_analyzer.py - add tests

@patch('syncopaid.screenshot_analyzer.ScreenshotAnalyzer._encode_image')
def test_analyzer_returns_blank_screen_on_low_confidence(mock_encode):
    """Test analyzer marks blank screens with failure_reason."""
    mock_llm = MagicMock()
    # LLM returns very low confidence (can't see anything useful)
    mock_llm.analyze_image.return_value = json.dumps({
        'confidence': 0.1,
        'visible_text': []
    })
    mock_encode.return_value = 'base64data'

    analyzer = ScreenshotAnalyzer(mock_llm)
    result = analyzer.analyze(Path('/fake/path.jpg'))

    assert result.confidence == 0.1
    assert result.failure_reason == "low_confidence"


@patch('syncopaid.screenshot_analyzer.ScreenshotAnalyzer._encode_image')
def test_analyzer_returns_api_error_on_exception(mock_encode):
    """Test analyzer handles LLM exceptions with failure_reason."""
    mock_llm = MagicMock()
    mock_llm.analyze_image.side_effect = Exception("API timeout")
    mock_encode.return_value = 'base64data'

    analyzer = ScreenshotAnalyzer(mock_llm)
    result = analyzer.analyze(Path('/fake/path.jpg'))

    assert result.confidence == 0.0
    assert result.failure_reason == "api_error"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_analyzer.py::test_analyzer_returns_blank_screen_on_low_confidence -v
```
Expected output: `FAILED` (AssertionError: assert None == "low_confidence")

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot_analyzer.py - modify analyze() method (around line 97-116)
    def analyze(self, image_path: Path) -> AnalysisResult:
        """
        Analyze a screenshot image.

        Args:
            image_path: Path to screenshot file

        Returns:
            AnalysisResult with extracted information
        """
        try:
            image_data = self._encode_image(image_path)
            response = self.llm_client.analyze_image(
                image_data=image_data,
                prompt=self._analysis_prompt
            )
            result = self._parse_response(response)

            # Detect low confidence as a failure
            if result.confidence < 0.3:
                result.failure_reason = "low_confidence"

            return result
        except Exception as e:
            logging.error(f"Screenshot analysis failed: {e}")
            return AnalysisResult(confidence=0.0, failure_reason="api_error")
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_analyzer.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/screenshot_analyzer.py tests/test_screenshot_analyzer.py && git commit -m "feat(8.6.5): detect and classify analysis failures"
```

---

### Task 3: Add failure_reason column to screenshots table (~3 min)

**Files:**
- Modify: `src/syncopaid/database_schema_screenshots.py`
- Test: `tests/test_database.py`

**Context:** The screenshots table needs a failure_reason column to persist why analysis failed. This is separate from analysis_status which tracks the processing state.

**Step 1 - RED:** Write failing test
```python
# tests/test_database.py - add to existing database tests
def test_screenshots_table_has_failure_reason_column(temp_db):
    """Test that screenshots table has failure_reason column after migration."""
    cursor = temp_db.conn.cursor()
    cursor.execute("PRAGMA table_info(screenshots)")
    columns = [row[1] for row in cursor.fetchall()]

    assert 'failure_reason' in columns
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database.py::test_screenshots_table_has_failure_reason_column -v
```
Expected output: `FAILED` (AssertionError: 'failure_reason' not in columns)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_schema_screenshots.py - modify _migrate_screenshots_table() (around line 44-59)
    def _migrate_screenshots_table(self):
        """Apply migrations to screenshots table for analysis support."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'analysis_data' not in columns:
                cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_data TEXT")
                logging.info("Migration: Added analysis_data column to screenshots")

            if 'analysis_status' not in columns:
                cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_status TEXT DEFAULT 'pending'")
                logging.info("Migration: Added analysis_status column to screenshots")

            if 'failure_reason' not in columns:
                cursor.execute("ALTER TABLE screenshots ADD COLUMN failure_reason TEXT")
                logging.info("Migration: Added failure_reason column to screenshots")

            conn.commit()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database.py::test_screenshots_table_has_failure_reason_column -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_schema_screenshots.py tests/test_database.py && git commit -m "feat(8.6.5): add failure_reason column to screenshots table"
```

---

### Task 4: Add update_screenshot_failure method to database (~4 min)

**Files:**
- Modify: `src/syncopaid/database_screenshots.py`
- Create: `tests/test_database_screenshots.py` (if not exists)

**Context:** Add a method to update screenshot analysis status to 'failed' with a failure reason. Separate from the existing update_screenshot_analysis which is for successful analyses.

**Step 1 - RED:** Write failing test
```python
# tests/test_database_screenshots.py - add test (create file if needed)
import pytest
from syncopaid.database import Database


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    return db


def test_update_screenshot_failure(temp_db):
    """Test updating screenshot with failure status and reason."""
    # Insert a test screenshot
    screenshot_id = temp_db.insert_screenshot(
        captured_at="2025-01-15T10:00:00",
        file_path="/fake/path.jpg"
    )

    # Mark as failed
    temp_db.update_screenshot_failure(
        screenshot_id=screenshot_id,
        failure_reason="low_confidence"
    )

    # Verify status and reason
    cursor = temp_db.conn.cursor()
    cursor.execute(
        "SELECT analysis_status, failure_reason FROM screenshots WHERE id = ?",
        (screenshot_id,)
    )
    row = cursor.fetchone()

    assert row[0] == 'failed'
    assert row[1] == 'low_confidence'


def test_update_screenshot_failure_clears_analysis_data(temp_db):
    """Test that failure clears any previous analysis data."""
    # Insert screenshot with previous analysis
    screenshot_id = temp_db.insert_screenshot(
        captured_at="2025-01-15T10:00:00",
        file_path="/fake/path.jpg"
    )
    temp_db.update_screenshot_analysis(
        screenshot_id=screenshot_id,
        analysis_data='{"application": "Word"}',
        analysis_status='completed'
    )

    # Mark as failed
    temp_db.update_screenshot_failure(
        screenshot_id=screenshot_id,
        failure_reason="api_error"
    )

    # Verify analysis_data cleared
    cursor = temp_db.conn.cursor()
    cursor.execute(
        "SELECT analysis_data FROM screenshots WHERE id = ?",
        (screenshot_id,)
    )
    row = cursor.fetchone()

    assert row[0] is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database_screenshots.py::test_update_screenshot_failure -v
```
Expected output: `FAILED` (AttributeError: 'Database' object has no attribute 'update_screenshot_failure')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_screenshots.py - add method after update_screenshot_analysis (around line 222)
    def update_screenshot_failure(
        self,
        screenshot_id: int,
        failure_reason: str
    ) -> None:
        """
        Mark a screenshot as failed analysis with a reason.

        Args:
            screenshot_id: ID of screenshot record
            failure_reason: Why analysis failed (e.g., "low_confidence", "api_error")
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots
                SET analysis_status = 'failed',
                    analysis_data = NULL,
                    failure_reason = ?
                WHERE id = ?
            """, (failure_reason, screenshot_id))
            conn.commit()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database_screenshots.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_screenshots.py tests/test_database_screenshots.py && git commit -m "feat(8.6.5): add update_screenshot_failure database method"
```

---

### Task 5: Add get_failed_screenshots query method (~4 min)

**Files:**
- Modify: `src/syncopaid/database_screenshots.py`
- Test: `tests/test_database_screenshots.py`

**Context:** The review interface needs to query screenshots that failed analysis. This method returns failed screenshots with their failure reasons.

**Step 1 - RED:** Write failing test
```python
# tests/test_database_screenshots.py - add test

def test_get_failed_screenshots(temp_db):
    """Test querying screenshots that failed analysis."""
    # Insert multiple screenshots with different statuses
    id1 = temp_db.insert_screenshot("2025-01-15T10:00:00", "/path1.jpg")
    id2 = temp_db.insert_screenshot("2025-01-15T11:00:00", "/path2.jpg")
    id3 = temp_db.insert_screenshot("2025-01-15T12:00:00", "/path3.jpg")

    # Mark some as failed
    temp_db.update_screenshot_failure(id1, "low_confidence")
    temp_db.update_screenshot_failure(id3, "api_error")
    # id2 stays pending

    # Query failed screenshots
    failed = temp_db.get_failed_screenshots()

    assert len(failed) == 2
    assert failed[0]['failure_reason'] == 'api_error'  # Most recent first
    assert failed[1]['failure_reason'] == 'low_confidence'


def test_get_failed_screenshots_empty_when_none_failed(temp_db):
    """Test get_failed_screenshots returns empty list when no failures."""
    temp_db.insert_screenshot("2025-01-15T10:00:00", "/path1.jpg")

    failed = temp_db.get_failed_screenshots()

    assert failed == []
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database_screenshots.py::test_get_failed_screenshots -v
```
Expected output: `FAILED` (AttributeError: 'Database' object has no attribute 'get_failed_screenshots')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_screenshots.py - add method after update_screenshot_failure
    def get_failed_screenshots(self, limit: int = 100) -> List[Dict]:
        """
        Get screenshots that failed analysis.

        Args:
            limit: Maximum number of screenshots to return

        Returns:
            List of screenshot records with id, file_path, failure_reason, captured_at
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, file_path, window_app, window_title, failure_reason, captured_at
                FROM screenshots
                WHERE analysis_status = 'failed'
                ORDER BY captured_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database_screenshots.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_screenshots.py tests/test_database_screenshots.py && git commit -m "feat(8.6.5): add get_failed_screenshots database method"
```

---

### Task 6: Add manual categorization method for failed screenshots (~3 min)

**Files:**
- Modify: `src/syncopaid/database_screenshots.py`
- Test: `tests/test_database_screenshots.py`

**Context:** Users need to manually categorize failed screenshots. This method updates a failed screenshot with manual analysis data and marks it as 'manual'.

**Step 1 - RED:** Write failing test
```python
# tests/test_database_screenshots.py - add test

def test_update_screenshot_manual_categorization(temp_db):
    """Test manually categorizing a failed screenshot."""
    screenshot_id = temp_db.insert_screenshot("2025-01-15T10:00:00", "/path1.jpg")
    temp_db.update_screenshot_failure(screenshot_id, "low_confidence")

    # Manually categorize
    manual_data = '{"application": "Microsoft Word", "document_name": "Brief.docx"}'
    temp_db.update_screenshot_manual(screenshot_id, manual_data)

    # Verify status changed and data saved
    cursor = temp_db.conn.cursor()
    cursor.execute(
        "SELECT analysis_status, analysis_data, failure_reason FROM screenshots WHERE id = ?",
        (screenshot_id,)
    )
    row = cursor.fetchone()

    assert row[0] == 'manual'
    assert row[1] == manual_data
    assert row[2] == 'low_confidence'  # Preserve original failure reason
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database_screenshots.py::test_update_screenshot_manual_categorization -v
```
Expected output: `FAILED` (AttributeError: 'Database' object has no attribute 'update_screenshot_manual')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_screenshots.py - add method
    def update_screenshot_manual(
        self,
        screenshot_id: int,
        analysis_data: str
    ) -> None:
        """
        Update a screenshot with manual categorization.

        Args:
            screenshot_id: ID of screenshot record
            analysis_data: JSON string of manually entered analysis
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE screenshots
                SET analysis_status = 'manual',
                    analysis_data = ?
                WHERE id = ?
            """, (analysis_data, screenshot_id))
            conn.commit()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database_screenshots.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_screenshots.py tests/test_database_screenshots.py && git commit -m "feat(8.6.5): add manual categorization method for failed screenshots"
```

---

### Task 7: Add "Needs Review" filter to ScreenshotReviewDialog (~7 min)

**Files:**
- Modify: `src/syncopaid/screenshot_review_dialog.py`
- Test: `tests/test_screenshot_review_dialog.py`

**Context:** The existing ScreenshotReviewDialog needs a new filter button to show screenshots that failed analysis. When clicked, it shows only failed screenshots with their failure reasons.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_review_dialog.py - add to existing tests
import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from syncopaid.screenshot_review_dialog import ScreenshotReviewDialog


@pytest.fixture
def mock_tk():
    """Create a mock Tk root for testing."""
    with patch('tkinter.Toplevel'):
        root = MagicMock(spec=tk.Tk)
        yield root


def test_dialog_has_needs_review_button(mock_tk):
    """Test that dialog has a 'Needs Review' filter button."""
    mock_db = MagicMock()
    mock_db.get_failed_screenshots.return_value = []

    dialog = ScreenshotReviewDialog(mock_tk, mock_db)

    # Check the class has the method for showing failed screenshots
    assert hasattr(dialog, '_show_failed')


def test_show_failed_calls_get_failed_screenshots(mock_tk):
    """Test that _show_failed calls the database method."""
    mock_db = MagicMock()
    mock_db.get_failed_screenshots.return_value = [
        {'id': 1, 'file_path': '/p.jpg', 'failure_reason': 'low_confidence', 'captured_at': '2025-01-15T10:00:00'}
    ]

    dialog = ScreenshotReviewDialog(mock_tk, mock_db)
    dialog.listbox = MagicMock()
    dialog.screenshots = []

    dialog._show_failed()

    mock_db.get_failed_screenshots.assert_called_once()
    assert len(dialog.screenshots) == 1
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_review_dialog.py::test_dialog_has_needs_review_button -v
```
Expected output: `FAILED` (AssertionError: False - no _show_failed method)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot_review_dialog.py - modify show() method to add button (around line 52)
        ttk.Button(filter_frame, text="All Dates", command=self._show_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Needs Review", command=self._show_failed).pack(side=tk.LEFT, padx=5)  # NEW

# Add new method after _show_all (around line 90)
    def _show_failed(self):
        """Show screenshots that failed analysis."""
        self.date_var.set('')  # Clear date filter
        self.screenshots = self.db.get_failed_screenshots()
        self._populate_listbox_with_failure()

    def _populate_listbox_with_failure(self):
        """Populate listbox showing failure reasons."""
        self.listbox.delete(0, tk.END)
        for screenshot in self.screenshots:
            failure = screenshot.get('failure_reason', 'unknown')
            display_text = f"{screenshot['captured_at'][:19]} - [{failure}] {screenshot.get('window_title', 'Unknown')}"
            self.listbox.insert(tk.END, display_text)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_review_dialog.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/screenshot_review_dialog.py tests/test_screenshot_review_dialog.py && git commit -m "feat(8.6.5): add Needs Review filter to screenshot review dialog"
```

---

### Task 8: Integration - Connect analyzer failures to database updates (~5 min)

**Files:**
- Create: `tests/test_analysis_failure_integration.py`
- Verify integration works end-to-end

**Context:** The analyzer returns AnalysisResult with failure_reason. The caller (likely night_processor or on-demand processor) needs to check for failure_reason and call the appropriate database method.

**Step 1 - RED:** Write integration test
```python
# tests/test_analysis_failure_integration.py
import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from syncopaid.screenshot_analyzer import ScreenshotAnalyzer, AnalysisResult
from syncopaid.database import Database


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    return db


def test_analysis_failure_flow(temp_db):
    """Test complete flow: analyze fails -> marked in database -> appears in review."""
    # Setup: Insert a screenshot
    screenshot_id = temp_db.insert_screenshot(
        captured_at="2025-01-15T10:00:00",
        file_path="/fake/screenshot.jpg"
    )

    # Create analyzer that returns low confidence
    mock_llm = MagicMock()
    mock_llm.analyze_image.return_value = json.dumps({
        'confidence': 0.1,
        'visible_text': []
    })

    with patch.object(ScreenshotAnalyzer, '_encode_image', return_value='base64data'):
        analyzer = ScreenshotAnalyzer(mock_llm)
        result = analyzer.analyze(Path("/fake/screenshot.jpg"))

    # Check result has failure
    assert result.failure_reason == "low_confidence"

    # Update database based on result
    if result.failure_reason:
        temp_db.update_screenshot_failure(screenshot_id, result.failure_reason)

    # Verify appears in failed list
    failed = temp_db.get_failed_screenshots()
    assert len(failed) == 1
    assert failed[0]['failure_reason'] == 'low_confidence'


def test_api_error_flow(temp_db):
    """Test API error -> failure marked in database."""
    screenshot_id = temp_db.insert_screenshot(
        captured_at="2025-01-15T10:00:00",
        file_path="/fake/screenshot.jpg"
    )

    mock_llm = MagicMock()
    mock_llm.analyze_image.side_effect = Exception("Timeout")

    with patch.object(ScreenshotAnalyzer, '_encode_image', return_value='base64data'):
        analyzer = ScreenshotAnalyzer(mock_llm)
        result = analyzer.analyze(Path("/fake/screenshot.jpg"))

    assert result.failure_reason == "api_error"

    if result.failure_reason:
        temp_db.update_screenshot_failure(screenshot_id, result.failure_reason)

    failed = temp_db.get_failed_screenshots()
    assert len(failed) == 1
    assert failed[0]['failure_reason'] == 'api_error'
```

**Step 2 - Verify tests pass:**
```bash
pytest tests/test_analysis_failure_integration.py -v
```
Expected output: All tests `PASSED`

**Step 3 - COMMIT:**
```bash
git add tests/test_analysis_failure_integration.py && git commit -m "test(8.6.5): add integration tests for analysis failure flow"
```

---

## Final Verification

Run the full test suite to ensure no regressions:
```bash
python -m pytest -v
```

All tests should pass. The following functionality is now implemented:
1. AnalysisResult includes failure_reason field
2. Analyzer detects and classifies failures (low_confidence, api_error)
3. Database schema includes failure_reason column
4. Database methods: update_screenshot_failure, get_failed_screenshots, update_screenshot_manual
5. Review dialog has "Needs Review" button to filter failed screenshots
6. Integration tests verify end-to-end flow

## Summary

| Task | Files Modified | Purpose |
|------|----------------|---------|
| 1 | screenshot_analyzer.py | Add failure_reason to AnalysisResult |
| 2 | screenshot_analyzer.py | Detect failures in analyze() |
| 3 | database_schema_screenshots.py | Add failure_reason column |
| 4 | database_screenshots.py | Add update_screenshot_failure() |
| 5 | database_screenshots.py | Add get_failed_screenshots() |
| 6 | database_screenshots.py | Add update_screenshot_manual() |
| 7 | screenshot_review_dialog.py | Add "Needs Review" filter |
| 8 | Integration test | Verify end-to-end flow |
