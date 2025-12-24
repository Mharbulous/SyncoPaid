# Browser URL Extraction - Part A: pywinauto Setup & Core Module

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Add pywinauto dependency and create the core URL extractor module with Chrome support.

**Tech Stack:** pywinauto | src/syncopaid/url_extractor.py

---

**Story ID:** 8.2 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Browser URL Extraction - Part A

**Description:**
**As a** developer
**I want** pywinauto installed and a basic URL extractor module
**So that** I can build browser URL extraction functionality

**Acceptance Criteria:**
- [ ] pywinauto added to requirements.txt
- [ ] url_extractor.py module created with Chrome support
- [ ] Basic tests for URL extraction function

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `requirements.txt` | Modify | Add pywinauto dependency |
| `tests/test_url_extractor.py` | Create | Test URL extraction logic |
| `src/syncopaid/url_extractor.py` | Create | Browser URL extraction module |

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

## Verification

- [ ] All tests pass: `python -m pytest tests/test_url_extractor.py -v`
- [ ] pywinauto imports correctly: `python -c "from syncopaid.url_extractor import extract_browser_url; print('OK')"`

## Next Sub-Plan

Continue with `020B_browser-url-multi-browser.md` for Edge/Firefox support and config toggle.
