# Resource Monitor Idle Optimization and Screenshot Throttling - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026_resource-usage-optimization.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add extended idle optimization, screenshot throttling support, and wire everything together in the main app.

**Approach:** Add get_idle_poll_interval method, add resource_monitor to ScreenshotWorker, then update main app to pass monitor to all components.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] 026A_resource-monitor-core.md completed
- [ ] 026B_resource-monitor-statistics.md completed
- [ ] 026C_resource-monitor-app-integration.md completed

## TDD Tasks

### Task 1: Add Extended Idle Optimization (~5 min)

**Files:**
- Modify: `tests/test_resource_monitor.py`
- Modify: `src/syncopaid/resource_monitor.py`

**Context:** Reduce polling frequency during extended idle periods (>10 minutes) to save resources when user is away.

**Step 1 - RED:** Write failing test
```python
# tests/test_resource_monitor.py (append to existing tests)

def test_get_idle_poll_interval():
    """Test get_idle_poll_interval returns slower interval for extended idle."""
    monitor = ResourceMonitor()

    # Short idle - normal interval
    short_idle_interval = monitor.get_idle_poll_interval(idle_seconds=60, base_interval=1.0)
    assert short_idle_interval == 1.0

    # Extended idle (>10 min) - slow interval
    extended_idle_interval = monitor.get_idle_poll_interval(idle_seconds=700, base_interval=1.0)
    assert extended_idle_interval == 10.0  # 10s for extended idle
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_resource_monitor.py::test_get_idle_poll_interval -v
```
Expected output: `FAILED` (method doesn't exist)

**Step 3 - GREEN:** Add idle optimization method
```python
# src/syncopaid/resource_monitor.py (add method to class)

    def get_idle_poll_interval(self, idle_seconds: float, base_interval: float = 1.0) -> float:
        """
        Get poll interval adjusted for idle time.

        During extended idle (>10 minutes), reduce polling from 1s to 10s
        to save resources when user is away.

        Args:
            idle_seconds: Current idle time in seconds
            base_interval: Normal poll interval (default 1.0s)

        Returns:
            Adjusted poll interval in seconds
        """
        # Extended idle threshold: 10 minutes
        EXTENDED_IDLE_THRESHOLD = 600  # 10 * 60 seconds
        IDLE_POLL_INTERVAL = 10.0

        if idle_seconds > EXTENDED_IDLE_THRESHOLD:
            return IDLE_POLL_INTERVAL

        return base_interval
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_resource_monitor.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_resource_monitor.py src/syncopaid/resource_monitor.py && git commit -m "feat: add extended idle optimization to reduce polling frequency"
```

---

### Task 2: Add Screenshot Throttling Support (~5 min)

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

### Task 3: Wire Everything Together in Main App (~5 min)

**Files:**
- Modify: `src/syncopaid/main_app_class.py`

**Context:** Pass the ResourceMonitor instance to TrackerLoop and ScreenshotWorker so all components share the same monitor.

**Step 1 - Verify current state:**
```bash
pytest tests/ -v --tb=short
```
Ensure all existing tests pass before final integration.

**Step 2 - Update main_app_class.py integration:**

Update ScreenshotWorker initialization:
```python
            self.screenshot_worker = ScreenshotWorker(
                screenshot_dir=screenshot_dir,
                db_insert_callback=self.database.insert_screenshot,
                threshold_identical=self.config.screenshot_threshold_identical,
                threshold_significant=self.config.screenshot_threshold_significant,
                threshold_identical_same_window=self.config.screenshot_threshold_identical_same_window,
                threshold_identical_different_window=self.config.screenshot_threshold_identical_different_window,
                quality=self.config.screenshot_quality,
                max_dimension=self.config.screenshot_max_dimension,
                resource_monitor=self.resource_monitor  # Add this line
            )
```

Update TrackerLoop initialization:
```python
        self.tracker = TrackerLoop(
            poll_interval=self.config.poll_interval_seconds,
            idle_threshold=self.config.idle_threshold_seconds,
            merge_threshold=self.config.merge_threshold_seconds,
            screenshot_worker=self.screenshot_worker,
            screenshot_interval=self.config.screenshot_interval_seconds,
            minimum_idle_duration=self.config.minimum_idle_duration_seconds,
            resource_monitor=self.resource_monitor  # Add this line
        )
```

**Important:** Move ResourceMonitor initialization BEFORE ScreenshotWorker and TrackerLoop initialization.

**Step 3 - Verify GREEN:**
```bash
pytest tests/ -v --tb=short
```
Expected output: All tests pass

**Step 4 - COMMIT:**
```bash
git add src/syncopaid/main_app_class.py && git commit -m "feat: wire ResourceMonitor to all tracking components"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid                    # App runs without error (Ctrl+C to exit)
```

Check logs for resource monitoring output:
```
ResourceMonitor initialized: cpu_threshold=80.0%, memory_threshold=200MB, battery_threshold=20%
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- psutil is already in the project dependencies (used for process info)
- Battery monitoring may return None on desktops without batteries - handled gracefully
- CPU monitoring needs one "priming" call before returning accurate values
- Resource statistics are logged on app shutdown for diagnostics
- Database VACUUM optimization (monthly) is deferred to a separate story to keep this focused
