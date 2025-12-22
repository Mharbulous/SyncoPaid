# Browser URL Extraction - Part C: Tracker Integration

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Integrate URL extraction into the tracker and respect config toggle.

**Tech Stack:** src/syncopaid/tracker.py | src/syncopaid/url_extractor.py

---

**Story ID:** 8.2 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Browser URL Extraction - Part C

**Description:**
**As a** user
**I want** URLs automatically captured when using browsers
**So that** my browsing activity is tracked with full context

**Acceptance Criteria:**
- [ ] get_active_window() includes URL for browsers
- [ ] URL extraction respects config toggle
- [ ] URLs stored in events table

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Part B completed: `020B_browser-url-multi-browser.md`
- [ ] Tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_tracker.py` | Modify | Test URL integration |
| `src/syncopaid/tracker.py` | Modify | Integrate URL extraction |

## TDD Tasks

### Task 1: Integrate URL Extraction in Tracker

**Files:** Test: `tests/test_tracker.py` | Impl: `src/syncopaid/tracker.py:129-160`

**RED:** Test that get_active_window() includes URL for browsers.
```python
def test_get_active_window_includes_url_for_chrome():
    """Should include URL when Chrome is active."""
    # Mock scenario: Chrome window active
    info = get_active_window()
    # URL should be present if Chrome, else None
    assert "url" in info
```
Run: `pytest tests/test_tracker.py::test_get_active_window_includes_url_for_chrome -v` → Expect: FAILED

**GREEN:** Modify get_active_window() to call extract_browser_url().
```python
def get_active_window() -> Dict[str, Optional[str]]:
    """
    Get information about the currently active window.

    Returns:
        Dictionary with 'app', 'title', and 'url' keys.
    """
    if not WINDOWS_APIS_AVAILABLE:
        return {"app": None, "title": None, "url": None}

    try:
        hwnd = win32gui.GetForegroundWindow()

        # Get window title
        title = win32gui.GetWindowText(hwnd)

        # Get process information
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        app = process.name()

        # Extract URL if browser and config enabled
        url = None
        # Import here to avoid circular dependency
        from .url_extractor import extract_browser_url
        # TODO: Check config.url_extraction_enabled
        url = extract_browser_url(app, timeout_ms=100)

        return {"app": app, "title": title, "url": url}

    except Exception as e:
        logger.debug(f"Error getting active window: {e}")
        return {"app": None, "title": None, "url": None}
```
Run: `pytest tests/test_tracker.py::test_get_active_window_includes_url_for_chrome -v` → Expect: PASSED

**COMMIT:** `git add tests/test_tracker.py src/syncopaid/tracker.py && git commit -m "feat: integrate URL extraction in tracker get_active_window"`

---

### Task 2: Respect Config Toggle in Tracker

**Files:** Test: `tests/test_tracker.py` | Impl: `src/syncopaid/tracker.py`

**RED:** Test that URL extraction respects config.
```python
def test_tracker_respects_url_config_disabled(tmp_path):
    """Should not extract URLs when disabled in config."""
    # Create config with url_extraction_enabled=False
    # Create TrackerLoop with that config
    # Verify URL is None even for browsers
    pass  # Implement based on TrackerLoop API
```

**GREEN:** Pass config to get_active_window() and check url_extraction_enabled.

**COMMIT:** `git add tests/test_tracker.py src/syncopaid/tracker.py && git commit -m "feat: respect url_extraction_enabled config in tracker"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.tracker` (verify URL captured for browsers)

## Next Sub-Plan

Continue with `020D_browser-url-performance.md` for performance validation.
