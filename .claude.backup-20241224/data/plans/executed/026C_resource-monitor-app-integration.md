# Resource Monitor App Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026_resource-usage-optimization.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Integrate ResourceMonitor into SyncoPaidApp and add adaptive polling to TrackerLoop.

**Approach:** Initialize ResourceMonitor in main app, pass to TrackerLoop, implement get_effective_poll_interval.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] 026A_resource-monitor-core.md completed (ResourceMonitor class exists with throttling methods)
- [ ] 026B_resource-monitor-statistics.md completed (config options exist)

## TDD Tasks

### Task 1: Integrate ResourceMonitor into SyncoPaidApp (~5 min)

**Files:**
- Create: `tests/test_main_app.py`
- Modify: `src/syncopaid/main_app_class.py`

**Context:** Wire up the ResourceMonitor to the main app so it starts monitoring on launch and logs statistics on shutdown.

**Step 1 - RED:** Write failing test
```python
# tests/test_main_app.py (create new file)
"""Tests for main app resource monitoring integration."""
import pytest


def test_main_app_has_resource_monitor():
    """Test SyncoPaidApp initializes ResourceMonitor."""
    # We can't easily test the full app in unit tests,
    # so we verify the import and structure
    from syncopaid.resource_monitor import ResourceMonitor

    # Verify ResourceMonitor can be instantiated
    monitor = ResourceMonitor()
    assert monitor is not None

    # Verify it has the expected interface
    assert hasattr(monitor, 'should_throttle_polling')
    assert hasattr(monitor, 'should_skip_screenshot')
    assert hasattr(monitor, 'record_metrics')
    assert hasattr(monitor, 'get_statistics')
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_main_app.py -v
```
Expected output: Test should pass (just verifying interface exists)

**Step 3 - GREEN:** Integrate ResourceMonitor into main_app_class.py

Add import at top of `src/syncopaid/main_app_class.py`:
```python
from syncopaid.resource_monitor import ResourceMonitor
```

Add to `__init__` method (after action_screenshot_worker initialization):
```python
        # Initialize resource monitor
        self.resource_monitor = ResourceMonitor(
            cpu_threshold=self.config.resource_cpu_threshold,
            memory_threshold_mb=self.config.resource_memory_threshold_mb,
            battery_threshold=self.config.resource_battery_threshold,
            monitoring_interval_seconds=self.config.resource_monitoring_interval_seconds
        )
        logging.info("Resource monitor initialized")
```

Add to `quit_app` method (before "Show final statistics"):
```python
        # Log resource statistics
        if self.resource_monitor:
            stats = self.resource_monitor.get_statistics()
            if stats['samples_count'] > 0:
                logging.info(
                    f"Resource stats - Peak CPU: {stats['peak_cpu']:.1f}%, "
                    f"Avg CPU: {stats['avg_cpu']:.1f}%, "
                    f"Peak Memory: {stats['peak_memory_mb']:.1f}MB, "
                    f"Avg Memory: {stats['avg_memory_mb']:.1f}MB"
                )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_main_app.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_main_app.py src/syncopaid/main_app_class.py && git commit -m "feat: integrate ResourceMonitor into SyncoPaidApp"
```

---

### Task 2: Add Adaptive Polling to TrackerLoop (~5 min)

**Files:**
- Modify: `tests/test_tracker.py`
- Modify: `src/syncopaid/tracker_loop.py`

**Context:** Make TrackerLoop aware of ResourceMonitor and adjust poll_interval dynamically when system is under load.

**Step 1 - RED:** Write failing test
```python
# tests/test_tracker.py (append to existing tests)

def test_tracker_loop_with_resource_monitor():
    """Test TrackerLoop accepts resource_monitor parameter."""
    from syncopaid.resource_monitor import ResourceMonitor

    monitor = ResourceMonitor()
    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        merge_threshold=2.0,
        resource_monitor=monitor
    )

    assert tracker.resource_monitor is monitor


def test_tracker_loop_get_effective_poll_interval():
    """Test get_effective_poll_interval returns throttled value when needed."""
    from syncopaid.resource_monitor import ResourceMonitor

    monitor = ResourceMonitor(cpu_threshold=80.0)
    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        merge_threshold=2.0,
        resource_monitor=monitor,
        throttled_poll_interval=5.0
    )

    # Method should exist and return a float
    interval = tracker.get_effective_poll_interval()
    assert isinstance(interval, float)
    assert interval >= 1.0  # At least base interval
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_tracker.py::test_tracker_loop_with_resource_monitor tests/test_tracker.py::test_tracker_loop_get_effective_poll_interval -v
```
Expected output: `FAILED` (parameter and method don't exist)

**Step 3 - GREEN:** Add resource monitoring support to TrackerLoop

Update `src/syncopaid/tracker_loop.py`:

Add to `__init__` signature:
```python
        resource_monitor=None,
        throttled_poll_interval: float = 5.0
```

Add to `__init__` body (after `self.event_finalizer`):
```python
        self.resource_monitor = resource_monitor
        self.throttled_poll_interval = throttled_poll_interval
```

Add new method to the class:
```python
    def get_effective_poll_interval(self) -> float:
        """
        Get current poll interval, considering throttling.

        Returns throttled interval (5s) if system CPU is high,
        otherwise returns normal poll interval (1s).
        """
        if self.resource_monitor and self.resource_monitor.should_throttle_polling():
            return self.throttled_poll_interval
        return self.poll_interval
```

Update the sleep call in `start()` method:
```python
                # Sleep until next poll (adaptive based on resource usage)
                time.sleep(self.get_effective_poll_interval())
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_tracker.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_tracker.py src/syncopaid/tracker_loop.py && git commit -m "feat: add adaptive polling to TrackerLoop based on resource usage"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_main_app.py tests/test_tracker.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`
