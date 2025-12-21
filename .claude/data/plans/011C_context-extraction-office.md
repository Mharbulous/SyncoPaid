# Context Extraction: Office File Paths - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add file path extraction from Office application window titles to context_extraction module.
**Approach:** Parse Word, Excel, PowerPoint window titles to extract file paths for AI categorization.
**Tech Stack:** Python string parsing, existing context_extraction.py module

---

**Story ID:** 1.6.3 | **Created:** 2025-12-21 | **Stage:** `planned`

---

## Story Context

**Title:** Office File Path Extraction

**Description:** **As a** lawyer using AI to categorize my time
**I want** file paths extracted from Office application window titles
**So that** the AI can match document work to client matter folders

**Acceptance Criteria:**
- [ ] Extract file paths from Word window titles
- [ ] Extract file paths from Excel window titles
- [ ] Extract file paths from PowerPoint window titles
- [ ] Handle filename-only titles (no full path)
- [ ] Return None for non-Office apps

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 1.6.1 (URL extraction) completed
- [ ] `src/syncopaid/context_extraction.py` exists

## TDD Tasks

### Task 1: Add Office file path extraction (~4 min)

**Files:**
- **Modify:** `test_context_extraction.py` (append new tests)
- **Modify:** `src/syncopaid/context_extraction.py` (add function)

**Context:** Office apps (Word, Excel, PowerPoint) show file paths in titles. Format: "Filename.docx - Word" or "C:\Path\To\File.xlsx - Excel". Extract the file path if present.

**Step 1 - RED:** Write failing test
```python
# test_context_extraction.py (add to end of file)

from syncopaid.context_extraction import extract_filepath_from_office

def test_extract_filepath_word_full_path():
    """Extract full file path from Word title."""
    title = "C:\\Matters\\1023-Smith\\Contract.docx - Word"
    result = extract_filepath_from_office("WINWORD.EXE", title)
    assert result == "C:\\Matters\\1023-Smith\\Contract.docx"

def test_extract_filepath_excel():
    """Extract file path from Excel title."""
    title = "D:\\Projects\\Budget-2024.xlsx - Excel"
    result = extract_filepath_from_office("EXCEL.EXE", title)
    assert result == "D:\\Projects\\Budget-2024.xlsx"

def test_extract_filepath_powerpoint():
    """Extract file path from PowerPoint title."""
    title = "Presentation.pptx - PowerPoint"
    result = extract_filepath_from_office("POWERPNT.EXE", title)
    assert result == "Presentation.pptx"

def test_extract_filepath_filename_only():
    """Extract filename when no directory path shown."""
    title = "Document1.docx - Word"
    result = extract_filepath_from_office("WINWORD.EXE", title)
    assert result == "Document1.docx"

def test_extract_filepath_non_office():
    """Return None for non-Office apps."""
    title = "Notepad"
    result = extract_filepath_from_office("notepad.exe", title)
    assert result is None

# Update main block to include new tests
if __name__ == "__main__":
    print("Running context extraction tests...")
    # ... existing tests ...
    test_extract_filepath_word_full_path()
    test_extract_filepath_excel()
    test_extract_filepath_powerpoint()
    test_extract_filepath_filename_only()
    test_extract_filepath_non_office()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_context_extraction.py
```
Expected output: `ImportError: cannot import name 'extract_filepath_from_office'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/context_extraction.py (add to end of file)

# Office application executable names
OFFICE_APPS = {
    'WINWORD.EXE': 'Word',
    'EXCEL.EXE': 'Excel',
    'POWERPNT.EXE': 'PowerPoint',
    'MSPUB.EXE': 'Publisher',
    'MSACCESS.EXE': 'Access'
}

def extract_filepath_from_office(app: str, title: str) -> str:
    """
    Extract file path from Office application window title.

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted file path/name, or None if not found
    """
    if not app or not title:
        return None

    # Check if this is an Office app
    app_upper = app.upper()
    if app_upper not in OFFICE_APPS:
        return None

    app_name = OFFICE_APPS[app_upper]

    # Format: "FILEPATH - AppName"
    separator = f" - {app_name}"
    if separator not in title:
        return None

    # Extract everything before the separator
    filepath = title.split(separator)[0].strip()

    if filepath:
        return filepath

    return None
```

**Step 4 - Verify GREEN:**
```bash
python test_context_extraction.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_context_extraction.py src/syncopaid/context_extraction.py && git commit -m "feat: add file path extraction from Office apps"
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
- Requires Story 1.6.1 (context_extraction module)
- Story 1.6.4 will create unified extract_context function
