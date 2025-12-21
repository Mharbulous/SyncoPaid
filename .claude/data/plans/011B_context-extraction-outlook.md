# Context Extraction: Outlook Email Subjects - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add email subject extraction from Outlook window titles to context_extraction module.
**Approach:** Parse Outlook window title formats to extract email subjects for AI categorization.
**Tech Stack:** Python string parsing, existing context_extraction.py module

---

**Story ID:** 1.6.2 | **Created:** 2025-12-21 | **Stage:** `planned`

---

## Story Context

**Title:** Outlook Email Subject Extraction

**Description:** **As a** lawyer using AI to categorize my time
**I want** email subjects extracted from Outlook window titles
**So that** the AI can match email activities to client matters

**Acceptance Criteria:**
- [ ] Extract subject from Outlook inbox view format
- [ ] Extract subject from Outlook message window format
- [ ] Return None for generic inbox without specific subject
- [ ] Handle non-Outlook apps gracefully

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 1.6.1 (URL extraction) completed
- [ ] `src/syncopaid/context_extraction.py` exists

## TDD Tasks

### Task 1: Add Outlook email subject extraction (~4 min)

**Files:**
- **Modify:** `test_context_extraction.py` (append new tests)
- **Modify:** `src/syncopaid/context_extraction.py` (add function)

**Context:** Outlook embeds email subjects in window titles. Format: "Inbox - RE: Subject Line - Outlook" or "Message Subject - Message - Outlook". Extract the subject portion between dashes.

**Step 1 - RED:** Write failing test
```python
# test_context_extraction.py (add to end of file)

from syncopaid.context_extraction import extract_subject_from_outlook

def test_extract_subject_inbox_format():
    """Extract subject from Outlook inbox view."""
    title = "Inbox - RE: Smith vs Jones Settlement - user@lawfirm.com - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result == "RE: Smith vs Jones Settlement"

def test_extract_subject_message_format():
    """Extract subject from Outlook message window."""
    title = "FW: Discovery Documents - Message (HTML) - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result == "FW: Discovery Documents"

def test_extract_subject_generic_inbox():
    """Return None for generic inbox without specific subject."""
    title = "Inbox - user@lawfirm.com - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result is None

def test_extract_subject_non_outlook():
    """Return None for non-Outlook apps."""
    title = "Email Subject - Thunderbird"
    result = extract_subject_from_outlook("thunderbird.exe", title)
    assert result is None

# Update main block to include new tests
if __name__ == "__main__":
    print("Running context extraction tests...")
    # ... existing tests ...
    test_extract_subject_inbox_format()
    test_extract_subject_message_format()
    test_extract_subject_generic_inbox()
    test_extract_subject_non_outlook()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_context_extraction.py
```
Expected output: `ImportError: cannot import name 'extract_subject_from_outlook'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/context_extraction.py (add to end of file)

def extract_subject_from_outlook(app: str, title: str) -> str:
    """
    Extract email subject from Outlook window title.

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted email subject, or None if no subject found
    """
    if not app or not title:
        return None

    # Check if this is Outlook
    if app.upper() != "OUTLOOK.EXE":
        return None

    # Format 1: "Inbox - SUBJECT - email@domain - Outlook"
    # Format 2: "SUBJECT - Message (HTML) - Outlook"

    # Remove trailing " - Outlook" first
    if title.endswith(" - Outlook"):
        title = title[:-10].strip()
    else:
        return None

    # Split by " - " separator
    parts = title.split(" - ")

    if len(parts) < 2:
        return None

    # Format 1: "Inbox - SUBJECT - email@domain"
    if parts[0] == "Inbox" and len(parts) >= 2:
        # Subject is second part, unless it's just an email
        subject = parts[1]
        # Skip if it's just an email address (no actual subject)
        if "@" in subject and len(parts) == 2:
            return None
        return subject

    # Format 2: "SUBJECT - Message (HTML)"
    if len(parts) >= 2 and "Message" in parts[-1]:
        return parts[0]

    return None
```

**Step 4 - Verify GREEN:**
```bash
python test_context_extraction.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: add email subject extraction from Outlook"
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
- Requires Story 1.6.1 (context_extraction module with URL extraction)
- Story 1.6.3 will add Office file path extraction
