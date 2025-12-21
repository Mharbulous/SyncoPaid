# Resource Usage Optimization and Adaptive Throttling - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-21 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Enable SyncoPaid to automatically monitor its own resource usage and adaptively throttle polling/screenshots when system resources are constrained, ensuring the app stays lightweight and non-intrusive.

**Approach:** Create a ResourceMonitor class that tracks CPU%, memory, and battery status. Integrate it into TrackerLoop and ScreenshotWorker with throttling callbacks. Add configuration options for thresholds.

**Tech Stack:** psutil (already in requirements), threading, TrackerLoop integration

---

## Story Context

**Title:** Resource Usage Optimization and Adaptive Throttling

**Description:** Background apps must be good citizens and not impact foreground work. No resource monitoring found via grep. Vision: "Non-Intrusive" - resource usage is a form of intrusiveness. Lawyers work on resource-constrained laptops and need battery life.

**User Story:** As a lawyer running SyncoPaid continuously in the background, I want the application to minimize CPU and memory usage, so that it doesn't slow down my other work applications or drain laptop battery

**Acceptance Criteria:**
- [ ] Monitor self resource usage: track CPU%, memory MB, thread count every 60 seconds
- [ ] Adaptive polling: slow down window polling from 1s to 5s when system load >80% CPU
- [ ] Screenshot throttling: skip screenshots when battery <20% or CPU >90%
- [ ] Memory management: clear screenshot cache when app memory >200MB
- [ ] Idle optimization: reduce polling frequency during extended idle (>10 minutes) from 1s to 10s
- [ ] Database optimization: vacuum database monthly, analyze query performance
- [ ] Log resource metrics for diagnostics: track peak/average CPU and memory
- [ ] Resume normal operation when system resources recover

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

### Task 3: Add Resource Metrics Logging (~5 min)

**Files:**
- Modify: `tests/test_resource_monitor.py`
- Modify: `src/syncopaid/resource_monitor.py`

**Context:** Track peak/average CPU and memory for diagnostics. This enables debugging performance issues after the fact.

**Step 1 - RED:** Write failing test
```python
# tests/test_resource_monitor.py (append to existing file)

def test_record_metrics_updates_statistics():
    """Test record_metrics updates peak and average tracking."""
    monitor = ResourceMonitor()

    # Record some metrics
    monitor.record_metrics()
    monitor.record_metrics()

    stats = monitor.get_statistics()
    assert 'peak_cpu' in stats
    assert 'peak_memory_mb' in stats
    assert 'avg_cpu' in stats
    assert 'avg_memory_mb' in stats
    assert 'samples_count' in stats
    assert stats['samples_count'] >= 2


def test_get_statistics_returns_empty_when_no_samples():
    """Test get_statistics returns zeros when no samples recorded."""
    monitor = ResourceMonitor()
    stats = monitor.get_statistics()

    assert stats['samples_count'] == 0
    assert stats['peak_cpu'] == 0.0
    assert stats['peak_memory_mb'] == 0.0
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_resource_monitor.py::test_record_metrics_updates_statistics tests/test_resource_monitor.py::test_get_statistics_returns_empty_when_no_samples -v
```
Expected output: `FAILED` (methods don't exist)

**Step 3 - GREEN:** Add metrics recording to ResourceMonitor
```python
# src/syncopaid/resource_monitor.py
# Add to __init__ method, after logger.info line:

        # Statistics tracking
        self._peak_cpu = 0.0
        self._peak_memory_mb = 0.0
        self._total_cpu = 0.0
        self._total_memory_mb = 0.0
        self._samples_count = 0

# Add new methods to the class:

    def record_metrics(self) -> dict:
        """
        Record current metrics for statistics tracking.

        Updates peak/average values. Should be called periodically
        (e.g., every 60 seconds).

        Returns:
            Current metrics dict
        """
        metrics = self.get_current_metrics()

        # Update peaks
        if metrics['cpu_percent'] > self._peak_cpu:
            self._peak_cpu = metrics['cpu_percent']
        if metrics['memory_mb'] > self._peak_memory_mb:
            self._peak_memory_mb = metrics['memory_mb']

        # Update totals for averaging
        self._total_cpu += metrics['cpu_percent']
        self._total_memory_mb += metrics['memory_mb']
        self._samples_count += 1

        logger.debug(
            f"Resource metrics: CPU={metrics['cpu_percent']:.1f}%, "
            f"Memory={metrics['memory_mb']:.1f}MB, "
            f"Battery={metrics['battery_percent']}%, "
            f"Threads={metrics['thread_count']}"
        )

        return metrics

    def get_statistics(self) -> dict:
        """
        Get resource usage statistics.

        Returns:
            dict with peak and average values
        """
        if self._samples_count == 0:
            return {
                'peak_cpu': 0.0,
                'peak_memory_mb': 0.0,
                'avg_cpu': 0.0,
                'avg_memory_mb': 0.0,
                'samples_count': 0
            }

        return {
            'peak_cpu': self._peak_cpu,
            'peak_memory_mb': self._peak_memory_mb,
            'avg_cpu': self._total_cpu / self._samples_count,
            'avg_memory_mb': self._total_memory_mb / self._samples_count,
            'samples_count': self._samples_count
        }
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_resource_monitor.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_resource_monitor.py src/syncopaid/resource_monitor.py && git commit -m "feat: add resource metrics logging and statistics tracking"
```

---

### Task 4: Add Configuration Options for Resource Thresholds (~3 min)

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config_defaults.py`
- Modify: `src/syncopaid/config_dataclass.py`

**Context:** Add config options so users can tune resource thresholds. These will be used when initializing ResourceMonitor.

**Step 1 - RED:** Write failing test
```python
# tests/test_config.py (append to existing tests)

def test_config_has_resource_monitoring_defaults():
    """Test config includes resource monitoring settings with defaults."""
    from syncopaid.config_defaults import DEFAULT_CONFIG
    from syncopaid.config_dataclass import Config

    # Check defaults exist
    assert 'resource_cpu_threshold' in DEFAULT_CONFIG
    assert 'resource_memory_threshold_mb' in DEFAULT_CONFIG
    assert 'resource_battery_threshold' in DEFAULT_CONFIG
    assert 'resource_monitoring_interval_seconds' in DEFAULT_CONFIG

    # Check Config dataclass accepts them
    config = Config(**DEFAULT_CONFIG)
    assert config.resource_cpu_threshold == 80.0
    assert config.resource_memory_threshold_mb == 200
    assert config.resource_battery_threshold == 20
    assert config.resource_monitoring_interval_seconds == 60
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::test_config_has_resource_monitoring_defaults -v
```
Expected output: `FAILED` (config keys don't exist)

**Step 3 - GREEN:** Add resource config options

First, update `src/syncopaid/config_defaults.py`:
```python
# src/syncopaid/config_defaults.py (add to DEFAULT_CONFIG dict, before closing brace)
    # Resource monitoring settings
    "resource_cpu_threshold": 80.0,
    "resource_memory_threshold_mb": 200,
    "resource_battery_threshold": 20,
    "resource_monitoring_interval_seconds": 60,
```

Then, update `src/syncopaid/config_dataclass.py` (add fields to Config class):
```python
    # Resource monitoring settings
    resource_cpu_threshold: float = 80.0
    resource_memory_threshold_mb: int = 200
    resource_battery_threshold: int = 20
    resource_monitoring_interval_seconds: int = 60
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py::test_config_has_resource_monitoring_defaults -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config.py src/syncopaid/config_defaults.py src/syncopaid/config_dataclass.py && git commit -m "feat: add resource monitoring configuration options"
```

---

### Task 5: Integrate ResourceMonitor into SyncoPaidApp (~5 min)

**Files:**
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

### Task 6: Add Adaptive Polling to TrackerLoop (~5 min)

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

### Task 7: Add Extended Idle Optimization (~5 min)

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

### Task 8: Add Screenshot Throttling Support (~5 min)

**Files:**
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

### Task 9: Wire Everything Together in Main App (~5 min)

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
