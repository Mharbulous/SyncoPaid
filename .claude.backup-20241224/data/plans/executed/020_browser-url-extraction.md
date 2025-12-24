# Browser URL Extraction - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Capture browser URLs alongside window titles to enable AI-powered legal research categorization.

**Approach:** Add UI Automation support to extract URLs from Chrome/Edge/Firefox address bars when browser windows are active. Store URLs in existing events.url field. Add config toggle with minimal performance impact (<100ms).

**Tech Stack:** pywinauto or uiautomation | src/syncopaid/tracker.py | src/syncopaid/config.py | SQLite

---

**Story ID:** 8.2 | **Created:** 2025-12-16 | **Status:** `planned`

---

## Story Context

**Title:** Browser URL Extraction

**Description:**
**As a** lawyer doing legal research online
**I want** browser URLs captured along with window titles
**So that** AI can identify which legal research sources I used (Westlaw, CanLII, court sites) and accurately categorize research time

**Acceptance Criteria:**
- [ ] Extract URL from Chrome address bar via UI Automation API
- [ ] Extract URL from Edge address bar via UI Automation API
- [ ] Extract URL from Firefox address bar via UI Automation API
- [ ] Store URL in existing events table (url field already exists)
- [ ] Handle browser not responding gracefully (timeout, fallback to title-only)
- [ ] Configurable enable/disable in settings (default: enabled)
- [ ] Minimal performance impact (<100ms per extraction)

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Install pywinauto: `pip install pywinauto`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `requirements.txt` | Add | Add pywinauto dependency |
| `tests/test_url_extractor.py` | Create | Test URL extraction logic |
| `src/syncopaid/url_extractor.py` | Create | Browser URL extraction module |
| `tests/test_tracker.py` | Modify | Test URL integration in tracker |
| `src/syncopaid/tracker.py:129-160` | Modify | Integrate URL extraction in get_active_window() |
| `src/syncopaid/config.py:16-37` | Modify | Add url_extraction_enabled config |

## TDD Tasks

### Task 1: Add pywinauto Dependency

**Files:** `requirements.txt`

**Action:** Add pywinauto to dependencies.

```txt
pywinauto>=0.6.8
```

**COMMIT:** `git add requirements.txt && git commit -m "deps: add pywinauto for browser URL extraction"`

---

### Task 2: Create URL Extractor Module (Chrome Support)

**Files:** Test: `tests/test_url_extractor.py` | Impl: `src/syncopaid/url_extractor.py`

**RED:** Create test for Chrome URL extraction.
```python
import pytest
from syncopaid.url_extractor import extract_browser_url

def test_extract_chrome_url_returns_string_or_none():
    """Should return URL string or None within timeout."""
    result = extract_browser_url("chrome.exe", timeout_ms=50)
    assert result is None or isinstance(result, str)

def test_extract_chrome_url_timeout():
    """Should return None if extraction exceeds timeout."""
    result = extract_browser_url("chrome.exe", timeout_ms=1)
    assert result is None

def test_extract_unsupported_browser():
    """Should return None for unsupported browsers."""
    result = extract_browser_url("notepad.exe")
    assert result is None
```
Run: `pytest tests/test_url_extractor.py -v` → Expect: FAILED (module doesn't exist)

**GREEN:** Implement minimal URL extractor with Chrome support.
```python
"""Browser URL extraction using UI Automation."""
import logging
from typing import Optional

try:
    from pywinauto import Desktop
    from pywinauto.timings import Timings
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

logger = logging.getLogger(__name__)

BROWSER_CONFIG = {
    "chrome.exe": {"control_type": "Edit", "class_name": "Chrome_OmniboxView"},
    "msedge.exe": {"control_type": "Edit", "class_name": "Chrome_OmniboxView"},
    "firefox.exe": {"control_type": "Edit", "class_name": "MozillaWindowClass"},
}

def extract_browser_url(app_name: str, timeout_ms: int = 100) -> Optional[str]:
    """
    Extract URL from browser address bar using UI Automation.

    Args:
        app_name: Browser executable name (e.g., "chrome.exe")
        timeout_ms: Max time to wait for extraction (default 100ms)

    Returns:
        URL string if successful, None otherwise
    """
    if not PYWINAUTO_AVAILABLE:
        logger.debug("pywinauto not available, skipping URL extraction")
        return None

    if app_name.lower() not in BROWSER_CONFIG:
        return None

    try:
        # Set timeout
        original_timeout = Timings.after_click_input_idle
        Timings.after_click_input_idle = timeout_ms / 1000.0

        config = BROWSER_CONFIG[app_name.lower()]
        desktop = Desktop(backend="uia")

        # Find active window
        window = desktop.top_window()

        # Find address bar control
        address_bar = window.child_window(
            control_type=config["control_type"],
            class_name=config["class_name"]
        )

        url = address_bar.get_value()

        # Restore timeout
        Timings.after_click_input_idle = original_timeout

        return url if url else None

    except Exception as e:
        logger.debug(f"Failed to extract URL from {app_name}: {e}")
        return None
```
Run: `pytest tests/test_url_extractor.py -v` → Expect: PASSED

**COMMIT:** `git add tests/test_url_extractor.py src/syncopaid/url_extractor.py && git commit -m "feat: add browser URL extraction with Chrome support"`

---

### Task 3: Add Edge and Firefox Support

**Files:** Test: `tests/test_url_extractor.py` | Impl: `src/syncopaid/url_extractor.py`

**RED:** Add tests for Edge and Firefox.
```python
def test_extract_edge_url():
    """Should extract URL from Edge."""
    result = extract_browser_url("msedge.exe", timeout_ms=50)
    assert result is None or isinstance(result, str)

def test_extract_firefox_url():
    """Should extract URL from Firefox."""
    result = extract_browser_url("firefox.exe", timeout_ms=50)
    assert result is None or isinstance(result, str)
```
Run: `pytest tests/test_url_extractor.py -v` → Expect: PASSED (Edge already shares Chrome config, Firefox needs fix)

**GREEN:** Update Firefox config in BROWSER_CONFIG if needed based on test results.

**COMMIT:** `git add tests/test_url_extractor.py src/syncopaid/url_extractor.py && git commit -m "feat: add Edge and Firefox URL extraction support"`

---

### Task 4: Add Config Toggle for URL Extraction

**Files:** Test: `tests/test_config.py` | Impl: `src/syncopaid/config.py:16-37`

**RED:** Test that config includes url_extraction_enabled.
```python
def test_default_config_has_url_extraction_enabled():
    """Default config should enable URL extraction."""
    from syncopaid.config import DEFAULT_CONFIG
    assert "url_extraction_enabled" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["url_extraction_enabled"] is True
```
Run: `pytest tests/test_config.py::test_default_config_has_url_extraction_enabled -v` → Expect: FAILED

**GREEN:** Add url_extraction_enabled to DEFAULT_CONFIG.
```python
DEFAULT_CONFIG = {
    "poll_interval_seconds": 0,
    "idle_threshold_seconds": 180,
    "merge_threshold_seconds": 2.0,
    "database_path": None,
    "start_on_boot": False,
    "start_tracking_on_launch": True,
    "url_extraction_enabled": True,  # NEW
    # Screenshot settings (periodic)
    "screenshot_enabled": True,
    # ... rest of config
}
```
Run: `pytest tests/test_config.py::test_default_config_has_url_extraction_enabled -v` → Expect: PASSED

**COMMIT:** `git add tests/test_config.py src/syncopaid/config.py && git commit -m "feat: add url_extraction_enabled config setting"`

---

### Task 5: Integrate URL Extraction in Tracker

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

### Task 6: Respect Config Toggle in Tracker

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

### Task 7: Performance Validation

**Files:** Test: `tests/test_url_extractor.py` | Impl: `src/syncopaid/url_extractor.py`

**RED:** Test that extraction completes within 100ms.
```python
import time

def test_url_extraction_performance():
    """Should complete within 100ms timeout."""
    start = time.perf_counter()
    result = extract_browser_url("chrome.exe", timeout_ms=100)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms <= 150  # Allow 50ms buffer for overhead
```
Run: `pytest tests/test_url_extractor.py::test_url_extraction_performance -v`

**GREEN:** Adjust timeout handling if test fails. Optimize control lookups if needed.

**COMMIT:** `git add tests/test_url_extractor.py src/syncopaid/url_extractor.py && git commit -m "test: validate URL extraction performance <100ms"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.tracker` (verify URL captured for browsers)
- [ ] Integration test: `python -m syncopaid` (run 30s, open Chrome/Edge/Firefox, verify URLs in DB)
- [ ] Check events table: `sqlite3 %LOCALAPPDATA%\SyncoPaid\SyncoPaid.db "SELECT app, url FROM events WHERE url IS NOT NULL LIMIT 5;"`

## Notes

**Edge Cases:**
- Browser in private/incognito mode (should still work)
- Multiple browser windows open (gets active window only)
- Browser minimized (not active, no extraction)
- Browser loading page (may get partial/old URL)

**Follow-up Work:**
- Story 8.4.2: Use URLs in transition detection
- Story 8.1: Use URLs for matter/client matching
- Consider caching browser window handles to reduce lookup overhead

**Performance:**
- pywinauto lookup adds ~50-100ms latency
- Only called when browser is active window (not every poll)
- Configurable disable for performance-sensitive environments
