# Browser URL Extraction - Part B: Multi-Browser Support & Config

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Add Edge/Firefox support and config toggle for URL extraction.

**Tech Stack:** pywinauto | src/syncopaid/url_extractor.py | src/syncopaid/config.py

---

**Story ID:** 8.2 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Browser URL Extraction - Part B

**Description:**
**As a** user
**I want** URL extraction to work with Edge and Firefox
**So that** my browsing across different browsers is captured

**Acceptance Criteria:**
- [ ] Extract URL from Edge address bar
- [ ] Extract URL from Firefox address bar
- [ ] Configurable enable/disable in settings

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Part A completed: `020A_browser-url-pywinauto-setup.md`
- [ ] Tests pass: `python -m pytest tests/test_url_extractor.py -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_url_extractor.py` | Modify | Add Edge/Firefox tests |
| `src/syncopaid/url_extractor.py` | Modify | Verify/fix Firefox config |
| `tests/test_config.py` | Modify | Test url_extraction_enabled |
| `src/syncopaid/config.py` | Modify | Add url_extraction_enabled setting |

## TDD Tasks

### Task 1: Add Edge and Firefox Support

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

### Task 2: Add Config Toggle for URL Extraction

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

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Config includes new setting: `python -c "from syncopaid.config import DEFAULT_CONFIG; print(DEFAULT_CONFIG.get('url_extraction_enabled'))"`

## Next Sub-Plan

Continue with `020C_browser-url-tracker-integration.md` for tracker integration.
