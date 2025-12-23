# Legal Context Test Foundation - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Create test file for context extraction and implement legal research app detection.

**Approach:** Create comprehensive test file, then add detection for legal research applications (desktop apps and browser patterns).

**Tech Stack:** Python regex | src/syncopaid/context_extraction.py | tests/test_context_extraction.py

---

**Story ID:** 1.7 | **Created:** 2025-12-23 | **Status:** `planned`

**Parent Plan:** 025_legal-context-extraction.md (decomposed)

---

## Story Context

**Title:** Application-Specific Context Extraction for Legal Tools

**Description:**
**As a** lawyer using legal research platforms like Westlaw and CanLII
**I want** the system to extract case citations, docket numbers, and research queries from specialized legal applications
**So that** the AI can automatically associate legal research time with the correct client matter

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_context_extraction.py` | Create | Test all context extraction functions |
| `src/syncopaid/context_extraction.py` | Modify | Add legal research detection |

## TDD Tasks

### Task 1: Create Test File for Context Extraction

**Files:** `tests/test_context_extraction.py`

**Action:** Create comprehensive test file covering existing and new extraction logic.

```python
"""Tests for context extraction from window titles."""
import pytest
from syncopaid.context_extraction import (
    extract_context,
    extract_url_from_browser,
    extract_subject_from_outlook,
    extract_filepath_from_office,
)


class TestBrowserURLExtraction:
    """Test browser URL extraction from titles."""

    def test_chrome_with_url_in_title(self):
        result = extract_url_from_browser("chrome.exe", "Google - https://google.com - Google Chrome")
        assert result == "https://google.com"

    def test_non_browser_returns_none(self):
        result = extract_url_from_browser("notepad.exe", "test.txt - Notepad")
        assert result is None


class TestOutlookSubjectExtraction:
    """Test Outlook email subject extraction."""

    def test_inbox_format(self):
        result = extract_subject_from_outlook("OUTLOOK.EXE", "Inbox - Meeting Request - user@law.com - Outlook")
        assert result == "Meeting Request"


class TestOfficeFilepathExtraction:
    """Test Office file path extraction."""

    def test_word_document(self):
        result = extract_filepath_from_office("WINWORD.EXE", "Smith-Contract.docx - Word")
        assert result == "Smith-Contract.docx"
```
Run: `pytest tests/test_context_extraction.py -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py && git commit -m "test: add context extraction test coverage"`

---

### Task 2: Add Legal Research App Detection

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Add tests for legal research app detection.
```python
class TestLegalResearchDetection:
    """Test legal research application detection."""

    @pytest.mark.parametrize("app_name", [
        "Westlaw.exe", "westlaw.exe", "WestlawNext.exe",
        "LexisNexis.exe", "lexisnexis.exe",
    ])
    def test_legal_app_detection_desktop(self, app_name):
        """Desktop apps should be detected."""
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app(app_name) is True

    @pytest.mark.parametrize("title_pattern", [
        "Westlaw - Search Results",
        "CanLII - 2024 BCSC 1234",
        "LexisNexis - Case Search",
        "Fastcase - Smith v. Jones",
        "Casetext - Legal Research",
    ])
    def test_legal_app_detection_browser(self, title_pattern):
        """Browser tabs with legal sites should be detected."""
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app("chrome.exe", title_pattern) is True

    def test_non_legal_app_not_detected(self):
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app("notepad.exe") is False
        assert is_legal_research_app("chrome.exe", "YouTube - Funny Video") is False
```
Run: `pytest tests/test_context_extraction.py::TestLegalResearchDetection -v` → Expect: FAILED

**GREEN:** Implement legal research app detection.
```python
# Legal research platforms (desktop apps and browser patterns)
LEGAL_RESEARCH_APPS = {
    'westlaw.exe', 'westlawnext.exe', 'lexisnexis.exe',
    'fastcase.exe', 'casetext.exe'
}

LEGAL_RESEARCH_BROWSER_PATTERNS = [
    'westlaw', 'canlii', 'lexisnexis', 'lexis+',
    'fastcase', 'casetext', 'courtlistener', 'justia'
]

def is_legal_research_app(app: str, title: str = None) -> bool:
    """
    Detect if window is a legal research application.

    Args:
        app: Application executable name
        title: Window title (optional, for browser detection)

    Returns:
        True if legal research app/site, False otherwise
    """
    if not app:
        return False

    # Check desktop apps
    if app.lower() in LEGAL_RESEARCH_APPS:
        return True

    # Check browser tabs for legal research sites
    if app.lower() in BROWSER_APPS and title:
        title_lower = title.lower()
        return any(pattern in title_lower for pattern in LEGAL_RESEARCH_BROWSER_PATTERNS)

    return False
```
Run: `pytest tests/test_context_extraction.py::TestLegalResearchDetection -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: add legal research app detection"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_context_extraction.py -v`
- [ ] Legal app detection working for desktop and browser

## Next Sub-Plan

After completing this sub-plan, continue with: `025B_legal-context-citation-extraction.md`
