# Context Extraction: Unified Function - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Create unified extract_context function that routes to appropriate extractor based on app type.
**Approach:** Single entry point function that checks app type and delegates to browser/Outlook/Office extractors.
**Tech Stack:** Python, existing context_extraction.py functions

---

**Story ID:** 1.6.4 | **Created:** 2025-12-21 | **Stage:** `planned`

---

## Story Context

**Title:** Unified Context Extraction Function

**Description:** **As a** developer integrating context extraction
**I want** a single entry point function that handles all app types
**So that** the tracker can call one function regardless of which app is active

**Acceptance Criteria:**
- [ ] Route browsers to URL extraction
- [ ] Route Outlook to subject extraction
- [ ] Route Office apps to filepath extraction
- [ ] Return None for unknown apps
- [ ] Handle None inputs gracefully

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 1.6.1 (URL extraction) completed
- [ ] Story 1.6.2 (Outlook extraction) completed
- [ ] Story 1.6.3 (Office extraction) completed

## TDD Tasks

### Task 1: Create unified extract_context function (~3 min)

**Files:**
- **Modify:** `test_context_extraction.py` (append new tests)
- **Modify:** `src/syncopaid/context_extraction.py` (add function)

**Context:** Create a single entry point function that routes to appropriate extractor based on app type. This will be called from tracker.py.

**Step 1 - RED:** Write failing test
```python
# test_context_extraction.py (add to end of file)

from syncopaid.context_extraction import extract_context

def test_extract_context_browser():
    """Route browser to URL extraction."""
    result = extract_context("chrome.exe", "Page - https://example.com - Chrome")
    assert result == "https://example.com"

def test_extract_context_outlook():
    """Route Outlook to subject extraction."""
    result = extract_context("OUTLOOK.EXE", "Inbox - RE: Case File - user@law.com - Outlook")
    assert result == "RE: Case File"

def test_extract_context_office():
    """Route Office to filepath extraction."""
    result = extract_context("WINWORD.EXE", "Contract.docx - Word")
    assert result == "Contract.docx"

def test_extract_context_unknown_app():
    """Return None for unknown apps."""
    result = extract_context("notepad.exe", "Untitled - Notepad")
    assert result is None

def test_extract_context_none_inputs():
    """Handle None inputs gracefully."""
    result = extract_context(None, None)
    assert result is None

# Update main block
if __name__ == "__main__":
    print("Running context extraction tests...")
    # ... existing tests ...
    test_extract_context_browser()
    test_extract_context_outlook()
    test_extract_context_office()
    test_extract_context_unknown_app()
    test_extract_context_none_inputs()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_context_extraction.py
```
Expected output: `ImportError: cannot import name 'extract_context'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/context_extraction.py (add to end of file)

def extract_context(app: str, title: str) -> str:
    """
    Extract contextual information from window title based on application type.

    Routes to appropriate extraction function:
    - Browsers → URL extraction
    - Outlook → Email subject extraction
    - Office apps → File path extraction

    Args:
        app: Application executable name (e.g., 'chrome.exe', 'OUTLOOK.EXE')
        title: Window title text

    Returns:
        Extracted context string (URL, subject, or filepath), or None if nothing extracted
    """
    if not app or not title:
        return None

    try:
        # Try browser URL extraction
        url = extract_url_from_browser(app, title)
        if url:
            return url

        # Try Outlook subject extraction
        subject = extract_subject_from_outlook(app, title)
        if subject:
            return subject

        # Try Office filepath extraction
        filepath = extract_filepath_from_office(app, title)
        if filepath:
            return filepath

        return None

    except Exception as e:
        # Log but don't crash - graceful degradation
        logging.debug(f"Context extraction failed for {app}: {e}")
        return None
```

**Step 4 - Verify GREEN:**
```bash
python test_context_extraction.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: add unified extract_context routing function"
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
- Requires Stories 1.6.1, 1.6.2, 1.6.3 completed
- Story 1.6.5 will integrate into tracker.py
