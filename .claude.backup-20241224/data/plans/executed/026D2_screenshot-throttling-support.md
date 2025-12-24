# Screenshot Throttling Support - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026D_resource-monitor-idle-screenshot.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add resource_monitor support to ScreenshotWorker so it can skip captures when battery is low or CPU is high.

**Approach:** Add resource_monitor parameter to WorkerState and ScreenshotWorker, then check constraints before capture.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] 026D1_extended-idle-optimization.md completed

## TDD Tasks

### Task 1: Add Screenshot Throttling Support (~5 min)

**Files:**
- Create: `tests/test_screenshot_throttling.py`
- Modify: `src/syncopaid/screenshot_worker_state.py`
- Modify: `src/syncopaid/screenshot.py`

**Context:** Pass resource_monitor to ScreenshotWorker so it can skip captures when battery is low or CPU is high.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_throttling.py (create new file)
"""Tests for screenshot resource throttling."""
import pytest


def test_screenshot_worker_accepts_resource_monitor():
    """Test ScreenshotWorker can accept resource_monitor parameter."""
    from syncopaid.resource_monitor import ResourceMonitor
    from syncopaid.screenshot_worker_state import WorkerState
    from pathlib import Path
    import tempfile

    monitor = ResourceMonitor()

    with tempfile.TemporaryDirectory() as tmpdir:
        state = WorkerState(
            screenshot_dir=Path(tmpdir),
            db_insert_callback=lambda **kwargs: None,
            resource_monitor=monitor
        )

        assert state.resource_monitor is monitor
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_throttling.py -v
```
Expected output: `FAILED` (parameter doesn't exist)

**Step 3 - GREEN:** Add resource_monitor support to WorkerState

Update `src/syncopaid/screenshot_worker_state.py`:

Add to `__init__` signature:
```python
        resource_monitor=None
```

Add to `__init__` body:
```python
        self.resource_monitor = resource_monitor
```

Update `src/syncopaid/screenshot.py` ScreenshotWorker class:

Add to `__init__` signature:
```python
        resource_monitor=None
```

Pass to WorkerState:
```python
        self._state = WorkerState(
            # ... existing params ...
            resource_monitor=resource_monitor
        )
```

In `_capture_and_compare` method, add after idle skip check:
```python
            # Skip if resources are constrained
            if self._state.resource_monitor and self._state.resource_monitor.should_skip_screenshot():
                logging.debug("Skipping screenshot: resource constraints")
                self._state.total_skipped += 1
                return
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_throttling.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_screenshot_throttling.py src/syncopaid/screenshot_worker_state.py src/syncopaid/screenshot.py && git commit -m "feat: add resource-based screenshot throttling"
```

---

## Final Verification

Run after task complete:
```bash
python -m pytest tests/test_screenshot_throttling.py -v  # Test passes
python -m pytest tests/ -v --tb=short  # All tests pass
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`
