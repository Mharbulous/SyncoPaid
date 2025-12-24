# Extended Idle Optimization - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026D_resource-monitor-idle-screenshot.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add get_idle_poll_interval method to ResourceMonitor to reduce polling frequency during extended idle periods.

**Approach:** Implement a simple method that returns slower polling interval when idle time exceeds 10 minutes.

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

## Final Verification

Run after task complete:
```bash
python -m pytest tests/test_resource_monitor.py -v  # All tests pass
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`
