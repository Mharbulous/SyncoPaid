# Legal Context Integration - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Extract docket/file numbers and integrate all legal extraction into the main extract_context function.

**Approach:** Implement docket number extraction, then create unified extract_legal_context function and integrate into main extract_context.

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

- [ ] Previous sub-plan completed: `025B_legal-context-citation-extraction.md`
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_context_extraction.py` | Modify | Add docket and integration tests |
| `src/syncopaid/context_extraction.py` | Modify | Add docket extraction and integration |

## TDD Tasks

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

## Verification

- [ ] All tests pass: `python -m pytest tests/test_context_extraction.py -v`
- [ ] Docket numbers extracted correctly
- [ ] Legal context integrates with main extract_context function

## Next Sub-Plan

After completing this sub-plan, continue with: `025D_legal-context-error-handling.md`
