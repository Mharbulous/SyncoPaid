# Browser URL Extraction - Part D: Performance Validation

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Validate and ensure URL extraction performance stays under 100ms.

**Tech Stack:** src/syncopaid/url_extractor.py

---

**Story ID:** 8.2 | **Created:** 2025-12-22 | **Status:** `planned`

---

## Story Context

**Title:** Browser URL Extraction - Part D

**Description:**
**As a** user
**I want** URL extraction to be fast
**So that** it doesn't impact application performance

**Acceptance Criteria:**
- [ ] URL extraction completes within 100ms
- [ ] Performance test validates timing
- [ ] Full integration verification passes

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Part C completed: `020C_browser-url-tracker-integration.md`
- [ ] Tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_url_extractor.py` | Modify | Add performance test |
| `src/syncopaid/url_extractor.py` | Modify | Optimize if needed |

## TDD Tasks

### Task 1: Performance Validation

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

## Final Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.tracker` (verify URL captured for browsers)
- [ ] Integration test: `python -m syncopaid` (run 30s, open Chrome/Edge/Firefox, verify URLs in DB)
- [ ] Check events table: `sqlite3 %LOCALAPPDATA%\SyncoPaid\SyncoPaid.db "SELECT app, url FROM events WHERE url IS NOT NULL LIMIT 5;"`

## Story Complete

After this sub-plan, Story 8.2 (Browser URL Extraction) is fully implemented:
- ✓ pywinauto dependency added
- ✓ URL extraction for Chrome, Edge, Firefox
- ✓ Config toggle for enable/disable
- ✓ Tracker integration
- ✓ Performance validation

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
