# Batch Analysis Foundation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.3 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 035_batch-processing-on-demand.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create foundation layer for batch analysis: database query method and progress tracking dataclass.

**Approach:** Add pending screenshot count method to database, create progress tracking dataclass with callbacks.

**Tech Stack:** Python 3.11+, SQLite

---

## Story Context

**Title:** Batch Processing On-Demand (Part 1 of 3)
**Description:** Foundation layer - database and progress tracking

**Acceptance Criteria:**
- [ ] Database can query count of pending screenshots
- [ ] Progress dataclass tracks processed/failed/cancelled state

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Add get_pending_screenshot_count to Database (~5 min)

**Files:**
- Modify: `src/syncopaid/database_screenshots.py`
- Test: `tests/test_database_screenshots.py`

**Context:** The NightProcessor needs to know how many screenshots are pending analysis. This method queries the database for screenshots with `analysis_status = 'pending'` or NULL.

**Step 1 - RED:** Write failing test
```python
# tests/test_database_screenshots.py - add to existing test class
def test_get_pending_screenshot_count_returns_count(self, db_with_screenshots):
    """Test that get_pending_screenshot_count returns correct count."""
    # Arrange: db_with_screenshots fixture creates 3 screenshots with NULL analysis_status

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 3


def test_get_pending_screenshot_count_excludes_completed(self, db_with_screenshots):
    """Test that completed screenshots are not counted."""
    # Arrange: Update one screenshot to 'completed'
    db_with_screenshots.conn.execute(
        "UPDATE screenshots SET analysis_status = 'completed' WHERE id = 1"
    )
    db_with_screenshots.conn.commit()

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_returns_count -v
```
Expected output: `FAILED` (AttributeError: 'Database' object has no attribute 'get_pending_screenshot_count')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_screenshots.py - add method to DatabaseScreenshotsMixin
def get_pending_screenshot_count(self) -> int:
    """
    Get count of screenshots pending analysis.

    Returns:
        Number of screenshots with analysis_status NULL or 'pending'
    """
    cursor = self.conn.execute("""
        SELECT COUNT(*) FROM screenshots
        WHERE analysis_status IS NULL OR analysis_status = 'pending'
    """)
    return cursor.fetchone()[0]
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_returns_count -v
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_excludes_completed -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_database_screenshots.py src/syncopaid/database_screenshots.py && git commit -m "feat(8.6.3): add get_pending_screenshot_count database method"
```

---

### Task 2: Create BatchAnalysisProgress dataclass (~3 min)

**Files:**
- Create: `src/syncopaid/batch_analysis_progress.py`
- Test: `tests/test_batch_analysis_progress.py`

**Context:** A dataclass to track batch analysis progress, supporting callbacks and cancellation. This decouples progress tracking from the NightProcessor.

**Step 1 - RED:** Write failing test
```python
# tests/test_batch_analysis_progress.py
import pytest
from syncopaid.batch_analysis_progress import BatchAnalysisProgress


def test_progress_initialization():
    """Test BatchAnalysisProgress initializes with correct values."""
    progress = BatchAnalysisProgress(total=100)

    assert progress.total == 100
    assert progress.processed == 0
    assert progress.failed == 0
    assert progress.is_cancelled is False
    assert progress.is_complete is False


def test_progress_update():
    """Test progress can be updated."""
    progress = BatchAnalysisProgress(total=10)

    progress.processed = 5
    progress.failed = 1

    assert progress.processed == 5
    assert progress.failed == 1
    assert progress.percent_complete == 50.0


def test_progress_cancel():
    """Test cancellation flag."""
    progress = BatchAnalysisProgress(total=10)

    progress.cancel()

    assert progress.is_cancelled is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_batch_analysis_progress.py -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.batch_analysis_progress')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/batch_analysis_progress.py
"""Batch analysis progress tracking."""
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class BatchAnalysisProgress:
    """
    Tracks progress of batch screenshot analysis.

    Attributes:
        total: Total screenshots to process
        processed: Number successfully processed
        failed: Number that failed
        is_cancelled: True if user cancelled
        is_complete: True when processing finished
        on_progress: Optional callback for progress updates
    """
    total: int
    processed: int = 0
    failed: int = 0
    is_cancelled: bool = False
    is_complete: bool = False
    on_progress: Optional[Callable[['BatchAnalysisProgress'], None]] = field(default=None, repr=False)

    @property
    def percent_complete(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.processed / self.total) * 100.0

    def cancel(self):
        """Request cancellation of processing."""
        self.is_cancelled = True

    def update(self, processed: int = None, failed: int = None):
        """Update progress and trigger callback."""
        if processed is not None:
            self.processed = processed
        if failed is not None:
            self.failed = failed
        if self.on_progress:
            self.on_progress(self)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_batch_analysis_progress.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/batch_analysis_progress.py tests/test_batch_analysis_progress.py && git commit -m "feat(8.6.3): add BatchAnalysisProgress dataclass for progress tracking"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_database_screenshots.py tests/test_batch_analysis_progress.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

This is sub-plan 1 of 3 for story 8.6.3. Next sub-plans:
- 035B: NightProcessor progress method + BatchAnalysisDialog UI
- 035C: Tray menu integration
