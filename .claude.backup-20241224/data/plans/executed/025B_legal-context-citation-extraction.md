# Legal Context Citation Extraction - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Extract Canadian and US case citations from legal research window titles.

**Approach:** Implement regex-based extraction for Canadian neutral citations (2024 BCSC 1234) and US case names (Smith v. Jones).

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

- [ ] Previous sub-plan completed: `025A_legal-context-test-foundation.md`
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_context_extraction.py` | Modify | Add citation extraction tests |
| `src/syncopaid/context_extraction.py` | Modify | Add citation extraction functions |

## TDD Tasks

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

## Verification

- [ ] All tests pass: `python -m pytest tests/test_context_extraction.py -v`
- [ ] Canadian citations extracted correctly
- [ ] US case names extracted correctly

## Next Sub-Plan

After completing this sub-plan, continue with: `025C_legal-context-integration.md`
