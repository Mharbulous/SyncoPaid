# Legal Context Error Handling - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Add comprehensive error handling tests and verify graceful failure for edge cases.

**Approach:** Test that extraction handles None values, empty strings, malformed input, and very long titles without crashing.

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

- [ ] Previous sub-plan completed: `025C_legal-context-integration.md`
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_context_extraction.py` | Modify | Add error handling tests |

## TDD Tasks

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

## Final Verification

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
