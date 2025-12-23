# Resource Monitor Statistics and Configuration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026_resource-usage-optimization.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add metrics logging/statistics tracking to ResourceMonitor and add configuration options for resource thresholds.

**Approach:** Add record_metrics and get_statistics methods, then add config defaults for resource thresholds.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] 026A_resource-monitor-core.md completed (ResourceMonitor class exists)

## TDD Tasks

### Task 1: Add Resource Metrics Logging (~5 min)

**Files:**
- Modify: `tests/test_resource_monitor.py`
- Modify: `src/syncopaid/resource_monitor.py`

**Context:** Track peak/average CPU and memory for diagnostics. This enables debugging performance issues after the fact.

**Step 1 - RED:** Write failing test
```python
# tests/test_resource_monitor.py (append to existing tests)

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

### Task 2: Add Configuration Options for Resource Thresholds (~3 min)

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_resource_monitor.py tests/test_config.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`
