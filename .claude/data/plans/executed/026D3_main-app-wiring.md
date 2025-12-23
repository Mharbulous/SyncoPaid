# Main App Component Wiring - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 9.5 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 026D_resource-monitor-idle-screenshot.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Wire the ResourceMonitor instance to TrackerLoop and ScreenshotWorker so all components share the same monitor.

**Approach:** Update main_app_class.py to pass resource_monitor to both TrackerLoop and ScreenshotWorker initializations.

**Tech Stack:** psutil (already in requirements)

---

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] 026D1_extended-idle-optimization.md completed
- [ ] 026D2_screenshot-throttling-support.md completed

## TDD Tasks

### Task 1: Wire Everything Together in Main App (~5 min)

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

Run after task complete:
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
