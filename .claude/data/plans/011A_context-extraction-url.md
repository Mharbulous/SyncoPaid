# Context Extraction: URL from Browsers - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Create a context_extraction module with URL extraction from browser window titles.
**Approach:** Create new module with function to extract URLs from Chrome, Edge, Firefox titles using regex patterns.
**Tech Stack:** Python regex (re module), existing tracker.py infrastructure

---

**Story ID:** 1.6.1 | **Created:** 2025-12-21 | **Stage:** `planned`

---

## Story Context

**Title:** URL Extraction from Browser Window Titles

**Description:** **As a** lawyer using AI to categorize my time
**I want** URLs extracted from browser window titles
**So that** the AI knows which websites I'm researching for client matters

**Acceptance Criteria:**
- [ ] Extract URLs from Chrome window titles
- [ ] Extract URLs from Edge window titles
- [ ] Extract URLs from Firefox window titles
- [ ] Handle browser windows without URLs gracefully

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Create context_extraction module with URL extraction function (~4 min)

**Files:**
- **Create:** `test_context_extraction.py`
- **Create:** `src/syncopaid/context_extraction.py`

**Context:** Browsers embed URLs in their window titles. Chrome: "Page Title - URL - Google Chrome", Edge: "Page Title - Microsoft Edge", Firefox: "Page Title - Mozilla Firefox". Extract URL if present.

**Step 1 - RED:** Write failing test
```python
# test_context_extraction.py
"""Test context extraction from window titles."""
import sys
sys.path.insert(0, 'src')

from syncopaid.context_extraction import extract_url_from_browser

def test_extract_url_chrome_with_url():
    """Extract URL from Chrome title with embedded URL."""
    title = "Smith vs Jones - CanLII - https://canlii.ca/t/abc123 - Google Chrome"
    result = extract_url_from_browser("chrome.exe", title)
    assert result == "https://canlii.ca/t/abc123"

def test_extract_url_chrome_without_url():
    """Return None when no URL pattern found."""
    title = "New Tab - Google Chrome"
    result = extract_url_from_browser("chrome.exe", title)
    assert result is None

def test_extract_url_edge():
    """Extract URL from Edge title."""
    title = "Case Law - https://www.courts.gov.bc.ca/decisions - Microsoft Edge"
    result = extract_url_from_browser("msedge.exe", title)
    assert result == "https://www.courts.gov.bc.ca/decisions"

def test_extract_url_firefox():
    """Extract URL from Firefox title."""
    title = "Research Document - https://example.com/doc - Mozilla Firefox"
    result = extract_url_from_browser("firefox.exe", title)
    assert result == "https://example.com/doc"

def test_extract_url_non_browser():
    """Return None for non-browser apps."""
    title = "Document.docx - Word"
    result = extract_url_from_browser("WINWORD.EXE", title)
    assert result is None

if __name__ == "__main__":
    print("Running context extraction tests...")
    test_extract_url_chrome_with_url()
    test_extract_url_chrome_without_url()
    test_extract_url_edge()
    test_extract_url_firefox()
    test_extract_url_non_browser()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_context_extraction.py
```
Expected output: `ModuleNotFoundError: No module named 'syncopaid.context_extraction'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/context_extraction.py
"""Extract contextual information from window titles."""
import re
import logging

# Browser executable names (case-insensitive matching)
BROWSER_APPS = {'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe'}

def extract_url_from_browser(app: str, title: str) -> str:
    """
    Extract URL from browser window title.

    Args:
        app: Application executable name (e.g., 'chrome.exe')
        title: Window title text

    Returns:
        Extracted URL string, or None if no URL found
    """
    if not app or not title:
        return None

    # Check if this is a browser
    if app.lower() not in BROWSER_APPS:
        return None

    # Pattern matches http:// or https:// URLs
    # Looks for protocol + domain + optional path
    url_pattern = r'https?://[^\s<>"\'\[\]{}|\\^`]+'

    match = re.search(url_pattern, title)
    if match:
        return match.group(0)

    return None
```

**Step 4 - Verify GREEN:**
```bash
python test_context_extraction.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: add URL extraction from browser titles"
```

---

## Final Verification

Run after task completes:
```bash
python test_context_extraction.py    # All unit tests pass
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

**Dependencies:**
- None - this is a new standalone module
- Story 1.6.2 will add Outlook extraction
- Story 1.6.3 will add Office file path extraction
