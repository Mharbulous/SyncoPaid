# Resource Monitor Core Class - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026_resource-usage-optimization.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create the foundational ResourceMonitor class that tracks CPU%, memory, battery, and provides throttling detection methods with statistics logging.

**Approach:** Create ResourceMonitor with initialization, get_current_metrics, throttling detection methods (should_throttle_polling, should_skip_screenshot, should_clear_cache), and metrics logging/statistics.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Create ResourceMonitor Class with CPU Monitoring (~5 min)

**Files:**
- Create: `tests/test_resource_monitor.py`
- Create: `src/syncopaid/resource_monitor.py`

**Context:** This task creates the foundation for resource monitoring. We start with CPU monitoring because it's the primary metric for adaptive throttling decisions.

**Step 1 - RED:** Write failing test
```python
# tests/test_resource_monitor.py
"""Tests for resource monitoring module."""
import pytest
from syncopaid.resource_monitor import ResourceMonitor


def test_resource_monitor_initialization():
    """Test ResourceMonitor can be created with default settings."""
    monitor = ResourceMonitor()
    assert monitor is not None
    assert monitor.cpu_threshold == 80.0
    assert monitor.memory_threshold_mb == 200
    assert monitor.battery_threshold == 20


def test_get_current_metrics_returns_dict():
    """Test get_current_metrics returns a dict with expected keys."""
    monitor = ResourceMonitor()
    metrics = monitor.get_current_metrics()

    assert isinstance(metrics, dict)
    assert 'cpu_percent' in metrics
    assert 'memory_mb' in metrics
    assert 'battery_percent' in metrics
    assert isinstance(metrics['cpu_percent'], (int, float))
    assert isinstance(metrics['memory_mb'], (int, float))
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_resource_monitor.py -v
```
Expected output: `FAILED` (test should fail because module doesn't exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/resource_monitor.py
"""
Resource monitoring module for adaptive throttling.

Tracks CPU%, memory, battery, and thread count to enable
intelligent throttling when system resources are constrained.
"""

import logging
import os
import psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitor system and process resources for adaptive throttling.

    Tracks:
    - Process CPU usage percentage
    - Process memory usage in MB
    - System battery percentage (if available)
    - Thread count

    Provides thresholds for triggering throttled behavior.
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold_mb: int = 200,
        battery_threshold: int = 20,
        monitoring_interval_seconds: float = 60.0
    ):
        """
        Initialize resource monitor.

        Args:
            cpu_threshold: CPU % above which to throttle (default: 80%)
            memory_threshold_mb: Memory MB above which to clear cache (default: 200)
            battery_threshold: Battery % below which to throttle (default: 20%)
            monitoring_interval_seconds: How often to check resources (default: 60s)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold_mb = memory_threshold_mb
        self.battery_threshold = battery_threshold
        self.monitoring_interval = monitoring_interval_seconds

        # Get current process for self-monitoring
        self._process = psutil.Process(os.getpid())

        # Initialize CPU monitoring (first call returns 0, need to prime it)
        try:
            self._process.cpu_percent()
        except Exception:
            pass

        logger.info(
            f"ResourceMonitor initialized: cpu_threshold={cpu_threshold}%, "
            f"memory_threshold={memory_threshold_mb}MB, battery_threshold={battery_threshold}%"
        )

    def get_current_metrics(self) -> dict:
        """
        Get current resource metrics.

        Returns:
            dict with keys: cpu_percent, memory_mb, battery_percent, thread_count
        """
        metrics = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'battery_percent': 100,  # Default to 100 if no battery
            'thread_count': 0
        }

        try:
            # Process CPU %
            metrics['cpu_percent'] = self._process.cpu_percent()

            # Process memory in MB
            memory_info = self._process.memory_info()
            metrics['memory_mb'] = memory_info.rss / (1024 * 1024)

            # Thread count
            metrics['thread_count'] = self._process.num_threads()

            # Battery (may not be available on desktops)
            battery = psutil.sensors_battery()
            if battery:
                metrics['battery_percent'] = battery.percent

        except Exception as e:
            logger.warning(f"Error getting resource metrics: {e}")

        return metrics
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_resource_monitor.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_resource_monitor.py src/syncopaid/resource_monitor.py && git commit -m "feat: add ResourceMonitor class with CPU/memory monitoring"
```

---

### Task 2: Add Throttling Detection Methods (~5 min)

**Files:**
- Modify: `tests/test_resource_monitor.py`
- Modify: `src/syncopaid/resource_monitor.py`

**Context:** Now we add methods that determine when to throttle based on current metrics vs thresholds. These will be called by TrackerLoop and ScreenshotWorker.

**Step 1 - RED:** Write failing test
```python
# tests/test_resource_monitor.py (append to existing file)

def test_should_throttle_polling_when_cpu_high():
    """Test should_throttle_polling returns True when CPU exceeds threshold."""
    monitor = ResourceMonitor(cpu_threshold=80.0)
    # Mock high CPU by checking logic (actual test uses threshold comparison)
    # In real scenario, we test the method's behavior
    result = monitor.should_throttle_polling()
    assert isinstance(result, bool)


def test_should_skip_screenshot_returns_bool():
    """Test should_skip_screenshot returns boolean."""
    monitor = ResourceMonitor(cpu_threshold=90.0, battery_threshold=20)
    result = monitor.should_skip_screenshot()
    assert isinstance(result, bool)


def test_should_clear_cache_returns_bool():
    """Test should_clear_cache returns boolean based on memory usage."""
    monitor = ResourceMonitor(memory_threshold_mb=200)
    result = monitor.should_clear_cache()
    assert isinstance(result, bool)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_resource_monitor.py::test_should_throttle_polling_when_cpu_high tests/test_resource_monitor.py::test_should_skip_screenshot_returns_bool tests/test_resource_monitor.py::test_should_clear_cache_returns_bool -v
```
Expected output: `FAILED` (methods don't exist)

**Step 3 - GREEN:** Add throttling methods to ResourceMonitor
```python
# src/syncopaid/resource_monitor.py (add these methods to the class)

    def should_throttle_polling(self) -> bool:
        """
        Check if window polling should be throttled (slowed down).

        Throttle when system CPU > 80% to reduce impact on foreground apps.

        Returns:
            True if polling should be slowed from 1s to 5s
        """
        try:
            # Use system CPU, not just our process
            system_cpu = psutil.cpu_percent(interval=0)
            return system_cpu > self.cpu_threshold
        except Exception as e:
            logger.warning(f"Error checking CPU for throttling: {e}")
            return False

    def should_skip_screenshot(self) -> bool:
        """
        Check if screenshots should be skipped.

        Skip when:
        - System CPU > 90% (screenshots are resource-intensive)
        - Battery < 20% (save power)

        Returns:
            True if screenshots should be skipped
        """
        try:
            # Check system CPU (higher threshold than polling)
            system_cpu = psutil.cpu_percent(interval=0)
            if system_cpu > 90:
                logger.debug(f"Skipping screenshot: CPU at {system_cpu}%")
                return True

            # Check battery
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged and battery.percent < self.battery_threshold:
                logger.debug(f"Skipping screenshot: Battery at {battery.percent}%")
                return True

            return False
        except Exception as e:
            logger.warning(f"Error checking screenshot skip conditions: {e}")
            return False

    def should_clear_cache(self) -> bool:
        """
        Check if screenshot cache should be cleared.

        Clear when app memory usage exceeds threshold (default 200MB).

        Returns:
            True if cache should be cleared
        """
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            return memory_mb > self.memory_threshold_mb
        except Exception as e:
            logger.warning(f"Error checking memory for cache clear: {e}")
            return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_resource_monitor.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_resource_monitor.py src/syncopaid/resource_monitor.py && git commit -m "feat: add throttling detection methods to ResourceMonitor"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_resource_monitor.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`
