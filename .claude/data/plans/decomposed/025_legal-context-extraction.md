# Legal Context Extraction - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Extract case citations, docket numbers, and search queries from legal research platforms (Westlaw, CanLII, LexisNexis, Fastcase, Casetext) to enable AI-powered matter matching.

**Approach:** Extend existing `context_extraction.py` with legal-specific extraction functions. Parse window titles for Canadian/US case citation formats, docket numbers, and research queries. Store in existing `url` field (contextual data). No schema changes needed.

**Tech Stack:** Python regex | src/syncopaid/context_extraction.py | tests/test_context_extraction.py

---

**Story ID:** 1.7 | **Created:** 2025-12-21 | **Status:** `planned`

---

## Story Context

**Title:** Application-Specific Context Extraction for Legal Tools

**Description:**
**As a** lawyer using legal research platforms like Westlaw and CanLII
**I want** the system to extract case citations, docket numbers, and research queries from specialized legal applications
**So that** the AI can automatically associate legal research time with the correct client matter

**Acceptance Criteria:**
- [ ] Detect legal research applications: Westlaw, CanLII, LexisNexis, Fastcase, Casetext
- [ ] Extract case citations from window titles (e.g., "2024 BCSC 1234", "Smith v. Jones")
- [ ] Parse docket/file numbers from court document viewers
- [ ] Capture search queries from legal databases when visible in title bar
- [ ] Store extracted legal_context in existing url field (ActivityEvent.url)
- [ ] Handle extraction failures gracefully (log, don't crash)

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_context_extraction.py` | Create | Test all context extraction functions |
| `src/syncopaid/context_extraction.py:127-168` | Modify | Add legal research extraction |

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

### Task 3: Extract Canadian Case Citations

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Test Canadian citation extraction.
```python
class TestCanadianCitationExtraction:
    """Test Canadian case citation extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("CanLII - 2024 BCSC 1234 - Google Chrome", "2024 BCSC 1234"),
        ("Westlaw - 2023 SCC 15 - Smith v Jones", "2023 SCC 15"),
        ("2022 ONCA 456 - Court of Appeal", "2022 ONCA 456"),
        ("R v Smith, 2021 ABQB 789", "2021 ABQB 789"),
        ("Decision - 2024 FC 100 - Federal Court", "2024 FC 100"),
    ])
    def test_neutral_citation_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_canadian_citation
        assert extract_canadian_citation(title) == expected

    def test_no_citation_returns_none(self):
        from syncopaid.context_extraction import extract_canadian_citation
        assert extract_canadian_citation("CanLII - Search Results") is None
```
Run: `pytest tests/test_context_extraction.py::TestCanadianCitationExtraction -v` → Expect: FAILED

**GREEN:** Implement Canadian citation extraction.
```python
# Canadian neutral citation pattern: YYYY CourtCode Number
# Examples: 2024 BCSC 1234, 2023 SCC 15, 2022 ONCA 456
CANADIAN_CITATION_PATTERN = re.compile(
    r'\b(20\d{2})\s+'  # Year (2000-2099)
    r'([A-Z]{2,6})\s+'  # Court code (2-6 uppercase letters)
    r'(\d{1,5})\b'       # Decision number
)

def extract_canadian_citation(title: str) -> str:
    """
    Extract Canadian neutral citation from window title.

    Examples: 2024 BCSC 1234, 2023 SCC 15, 2022 ONCA 456

    Args:
        title: Window title text

    Returns:
        Citation string (e.g., "2024 BCSC 1234") or None
    """
    if not title:
        return None

    match = CANADIAN_CITATION_PATTERN.search(title)
    if match:
        year, court, number = match.groups()
        return f"{year} {court} {number}"

    return None
```
Run: `pytest tests/test_context_extraction.py::TestCanadianCitationExtraction -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: extract Canadian neutral citations from legal tools"`

---

### Task 4: Extract US Case Citations

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Test US citation extraction.
```python
class TestUSCitationExtraction:
    """Test US case citation extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("Westlaw - Brown v. Board of Education", "Brown v. Board of Education"),
        ("Smith v. Jones - LexisNexis", "Smith v. Jones"),
        ("Re: Matter of Johnson", "Matter of Johnson"),
        ("In re Application of Smith", "In re Application of Smith"),
    ])
    def test_case_name_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_case_name
        assert extract_case_name(title) == expected

    def test_no_case_name_returns_none(self):
        from syncopaid.context_extraction import extract_case_name
        assert extract_case_name("Westlaw - Home Page") is None
```
Run: `pytest tests/test_context_extraction.py::TestUSCitationExtraction -v` → Expect: FAILED

**GREEN:** Implement US case name extraction.
```python
# Case name patterns: Party v. Party, In re X, Matter of X
CASE_NAME_PATTERN = re.compile(
    r'\b('
    r'[A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)*'  # First party
    r'\s+v\.?\s+'                                     # "v" or "v."
    r'[A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)*'  # Second party
    r'|'
    r'(?:In\s+re|Matter\s+of|Re:?\s*)'               # In re / Matter of
    r'\s+[A-Z][a-zA-Z\'\-\s]+'                        # Subject
    r')\b'
)

def extract_case_name(title: str) -> str:
    """
    Extract US-style case name from window title.

    Examples: Smith v. Jones, In re Application of Smith

    Args:
        title: Window title text

    Returns:
        Case name string or None
    """
    if not title:
        return None

    match = CASE_NAME_PATTERN.search(title)
    if match:
        case_name = match.group(1).strip()
        # Clean up trailing punctuation
        case_name = re.sub(r'[\s\-]+$', '', case_name)
        return case_name if len(case_name) > 5 else None

    return None
```
Run: `pytest tests/test_context_extraction.py::TestUSCitationExtraction -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: extract US case names from legal tools"`

---

### Task 5: Extract Docket/File Numbers

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Test docket number extraction.
```python
class TestDocketNumberExtraction:
    """Test court docket/file number extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("Case No. 2024-CV-12345", "2024-CV-12345"),
        ("Docket: 1:24-cv-00123", "1:24-cv-00123"),
        ("File No. CV-2024-001234", "CV-2024-001234"),
        ("Court File No. SC-24-123456", "SC-24-123456"),
    ])
    def test_docket_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_docket_number
        assert extract_docket_number(title) == expected

    def test_no_docket_returns_none(self):
        from syncopaid.context_extraction import extract_docket_number
        assert extract_docket_number("General Legal Document") is None
```
Run: `pytest tests/test_context_extraction.py::TestDocketNumberExtraction -v` → Expect: FAILED

**GREEN:** Implement docket number extraction.
```python
# Docket/file number patterns
DOCKET_PATTERN = re.compile(
    r'(?:Case\s+No\.?|Docket:?|File\s+No\.?|Court\s+File\s+No\.?)\s*'
    r'([A-Z0-9\-:]+)',
    re.IGNORECASE
)

def extract_docket_number(title: str) -> str:
    """
    Extract court docket/file number from window title.

    Examples: 2024-CV-12345, 1:24-cv-00123

    Args:
        title: Window title text

    Returns:
        Docket number string or None
    """
    if not title:
        return None

    match = DOCKET_PATTERN.search(title)
    if match:
        docket = match.group(1).strip()
        # Must have at least one digit to be a valid docket
        if re.search(r'\d', docket):
            return docket

    return None
```
Run: `pytest tests/test_context_extraction.py::TestDocketNumberExtraction -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: extract docket/file numbers from court documents"`

---

### Task 6: Integrate Legal Extraction into Main Function

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Test that extract_context() includes legal research extraction.
```python
class TestLegalContextIntegration:
    """Test legal context integration in main extract_context function."""

    def test_canlii_citation_extracted(self):
        result = extract_context("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome")
        assert "2024 BCSC 1234" in result

    def test_westlaw_case_name_extracted(self):
        result = extract_context("chrome.exe", "Westlaw - Smith v. Jones - Edge")
        assert "Smith v. Jones" in result

    def test_docket_number_extracted(self):
        result = extract_context("chrome.exe", "Case No. 2024-CV-12345 - Court Portal")
        assert "2024-CV-12345" in result

    def test_legal_desktop_app(self):
        result = extract_context("westlaw.exe", "Research: Smith v. Jones - 2024 SCC 15")
        assert result is not None
```
Run: `pytest tests/test_context_extraction.py::TestLegalContextIntegration -v` → Expect: FAILED

**GREEN:** Update extract_context() to include legal extraction.
```python
def extract_legal_context(app: str, title: str) -> str:
    """
    Extract legal research context from window title.

    Combines multiple extraction strategies:
    1. Canadian neutral citations (2024 BCSC 1234)
    2. US case names (Smith v. Jones)
    3. Docket/file numbers (2024-CV-12345)

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted legal context or None
    """
    if not is_legal_research_app(app, title):
        return None

    # Priority order: Citations > Case Names > Docket Numbers
    citation = extract_canadian_citation(title)
    if citation:
        return citation

    case_name = extract_case_name(title)
    if case_name:
        return case_name

    docket = extract_docket_number(title)
    if docket:
        return docket

    return None


def extract_context(app: str, title: str) -> str:
    """
    Extract contextual information from window title.

    Routes to appropriate extraction function:
    - Legal research → Citation/case name/docket extraction
    - Browsers → URL extraction
    - Outlook → Email subject extraction
    - Office apps → File path extraction

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted context string or None
    """
    if not app or not title:
        return None

    try:
        # Try legal research extraction first (highest value)
        legal = extract_legal_context(app, title)
        if legal:
            return legal

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
        logging.debug(f"Context extraction failed for {app}: {e}")
        return None
```
Run: `pytest tests/test_context_extraction.py::TestLegalContextIntegration -v` → Expect: PASSED

**COMMIT:** `git add tests/test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: integrate legal context extraction into main function"`

---

### Task 7: Add Graceful Error Handling

**Files:** Test: `tests/test_context_extraction.py` | Impl: `src/syncopaid/context_extraction.py`

**RED:** Test that extraction handles edge cases gracefully.
```python
class TestGracefulErrorHandling:
    """Test extraction handles edge cases without crashing."""

    def test_none_app_returns_none(self):
        assert extract_context(None, "Some Title") is None

    def test_none_title_returns_none(self):
        assert extract_context("chrome.exe", None) is None

    def test_empty_title_returns_none(self):
        assert extract_context("chrome.exe", "") is None

    def test_malformed_citation_graceful(self):
        # Should not crash on malformed input
        result = extract_context("chrome.exe", "20XX FAKE ####")
        assert result is None or isinstance(result, str)

    def test_very_long_title_graceful(self):
        long_title = "A" * 10000
        result = extract_context("chrome.exe", long_title)
        assert result is None or isinstance(result, str)
```
Run: `pytest tests/test_context_extraction.py::TestGracefulErrorHandling -v` → Expect: PASSED (existing error handling should work)

**COMMIT:** `git add tests/test_context_extraction.py && git commit -m "test: verify graceful error handling in context extraction"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_context_extraction.py -v`
- [ ] Integration test: `python -m syncopaid.tracker` (open browser to CanLII/Westlaw, verify citation in output)
- [ ] Full test suite: `python -m pytest tests/ -v`

## Notes

**Supported Legal Platforms:**
- Desktop: Westlaw, WestlawNext, LexisNexis, Fastcase, Casetext
- Browser: CanLII, Westlaw, LexisNexis, Lexis+, Fastcase, Casetext, CourtListener, Justia

**Citation Formats:**
- Canadian neutral: 2024 BCSC 1234, 2023 SCC 15
- US case names: Smith v. Jones, In re Application
- Docket numbers: 2024-CV-12345, 1:24-cv-00123

**Design Decisions:**
- Uses existing `url` field (ActivityEvent.url) for legal context
- No schema migration needed
- Legal context takes priority over URL in extract_context() since it's higher value for billing

**Follow-up Work:**
- Story 15.3: Use legal context for client/matter matching
- Consider adding more court codes for provincial courts
- Could extract additional metadata (judge names, dates) in future
