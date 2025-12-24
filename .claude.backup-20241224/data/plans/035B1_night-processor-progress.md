# NightProcessor Progress Support - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.3 | **Created:** 2025-12-24 | **Stage:** `planned`
**Parent Plan:** 035B_batch-analysis-processor-ui.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add progress-aware batch processing method to NightProcessor.

**Approach:** Extend NightProcessor with process_batch_with_progress method that supports progress callbacks and cancellation.

**Tech Stack:** Python 3.11+

---

## Story Context

**Title:** Batch Processing On-Demand (Part 2 of 3) - Sub-plan 1
**Description:** Processing layer - NightProcessor extension with progress support

**Acceptance Criteria:**
- [ ] NightProcessor supports progress callbacks
- [ ] NightProcessor respects cancellation token

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Sub-plan 035A completed (BatchAnalysisProgress dataclass exists)

## TDD Tasks

### Task 1: Add process_batch_with_progress to NightProcessor (~5 min)

**Files:**
- Modify: `src/syncopaid/night_processor.py`
- Test: `tests/test_night_processor.py`

**Context:** Extend NightProcessor with a method that supports progress tracking and cancellation. This wraps the existing processing logic with progress callbacks.

**Step 1 - RED:** Write failing test
```python
# tests/test_night_processor.py - add test
from syncopaid.batch_analysis_progress import BatchAnalysisProgress


def test_process_batch_with_progress_reports_progress():
    """Test that process_batch_with_progress calls progress callback."""
    progress_updates = []

    def mock_process_batch(batch_size: int) -> int:
        return 5  # Simulate processing 5 items

    def mock_get_pending_count() -> int:
        return 10

    processor = NightProcessor(
        get_pending_count=mock_get_pending_count,
        process_batch=mock_process_batch,
        batch_size=5
    )

    progress = BatchAnalysisProgress(
        total=10,
        on_progress=lambda p: progress_updates.append(p.processed)
    )

    processor.process_batch_with_progress(progress)

    assert len(progress_updates) > 0
    assert progress.is_complete is True


def test_process_batch_with_progress_respects_cancellation():
    """Test that cancellation stops processing."""
    process_count = [0]

    def mock_process_batch(batch_size: int) -> int:
        process_count[0] += 1
        return batch_size

    def mock_get_pending_count() -> int:
        return 100  # Many items

    processor = NightProcessor(
        get_pending_count=mock_get_pending_count,
        process_batch=mock_process_batch,
        batch_size=5
    )

    progress = BatchAnalysisProgress(total=100)
    progress.cancel()  # Cancel immediately

    processor.process_batch_with_progress(progress)

    assert process_count[0] == 0  # Should not process anything
    assert progress.is_complete is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_night_processor.py::test_process_batch_with_progress_reports_progress -v
```
Expected output: `FAILED` (AttributeError: 'NightProcessor' object has no attribute 'process_batch_with_progress')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/night_processor.py - add import at top
from syncopaid.batch_analysis_progress import BatchAnalysisProgress

# Add method to NightProcessor class (after trigger_manual method)
def process_batch_with_progress(self, progress: BatchAnalysisProgress) -> int:
    """
    Process screenshots with progress tracking and cancellation support.

    Args:
        progress: BatchAnalysisProgress instance for tracking

    Returns:
        Total number of screenshots processed
    """
    if self._process_batch is None:
        progress.is_complete = True
        return 0

    total_processed = 0

    while not progress.is_cancelled:
        if self._get_pending_count is None:
            break

        pending = self._get_pending_count()
        if pending == 0:
            break

        batch_processed = self._process_batch(self.batch_size)
        total_processed += batch_processed
        progress.update(processed=total_processed)

        if batch_processed == 0:
            break

    progress.is_complete = True
    progress.update()  # Final update
    return total_processed
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_night_processor.py::test_process_batch_with_progress_reports_progress -v
pytest tests/test_night_processor.py::test_process_batch_with_progress_respects_cancellation -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/night_processor.py tests/test_night_processor.py && git commit -m "feat(8.6.3): add process_batch_with_progress with cancellation support"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_night_processor.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

This is sub-plan 1 of 2 for 035B (story 8.6.3). Next sub-plan:
- 035B2: BatchAnalysisDialog UI
