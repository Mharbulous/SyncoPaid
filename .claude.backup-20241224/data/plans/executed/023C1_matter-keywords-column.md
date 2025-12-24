# 023C1: Matter Keywords Column in Treeview

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add a Keywords (AI) column to the MatterDialog treeview to display AI-extracted keywords.
**Approach:** Modify MatterDialog in matter_client_dialog_matters.py to include keywords column.
**Tech Stack:** tkinter (existing UI framework)

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** Keywords displayed in matter list UI (read-only, AI-managed). Users see the keywords but cannot edit them - AI has complete control.

**Acceptance Criteria:**
- [ ] Keywords displayed in matter list UI (read-only, AI-managed)
- [ ] Keywords are clearly labeled as AI-generated

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023A complete (matter_keywords table exists)
- [ ] Sub-plan 023B complete (keyword extraction works)
- [ ] Format functions exist: `format_keywords_for_display`, `get_matters_with_keywords` in matter_client_dialog.py
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Add Keywords column to MatterDialog treeview (~5 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog_matters.py`
- Test: `tests/test_matter_keywords.py`

**Context:** MatterDialog uses tkinter Treeview to display matters. We need to add a "Keywords (AI)" column showing the formatted keywords. The column header indicates these are AI-managed. The format functions already exist in matter_client_dialog.py.

**Step 1 - RED:** Write failing test
```python
# tests/test_matter_keywords.py (ADD to existing file)

def test_matter_dialog_has_keywords_column():
    """Test that MatterDialog includes a Keywords column."""
    # This test verifies the column configuration exists
    from syncopaid.matter_client_dialog_matters import MatterDialog

    # Check that MatterDialog has keywords in its column configuration
    # by examining the class constants or configuration
    import inspect
    source = inspect.getsource(MatterDialog)

    # Verify keywords column is defined
    assert 'keywords' in source.lower(), "MatterDialog should have keywords column"
    assert 'Keywords (AI)' in source or 'keywords' in source.lower(), "Column should be labeled as AI-managed"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_matter_keywords.py::test_matter_dialog_has_keywords_column -v
```
Expected output: `FAILED` (keywords column not yet added)

**Step 3 - GREEN:** Modify MatterDialog to add Keywords column

First, examine the current MatterDialog structure:
```bash
grep -n "columns" src/syncopaid/matter_client_dialog_matters.py
grep -n "Treeview" src/syncopaid/matter_client_dialog_matters.py
grep -n "_refresh" src/syncopaid/matter_client_dialog_matters.py
```

Then modify MatterDialog._create_treeview to add Keywords column:

```python
# In MatterDialog._create_treeview method, update columns tuple:
# Add 'keywords' to the columns list
# Example change (actual line numbers may vary):
columns = ("matter_number", "client", "description", "keywords", "status")

# Add column heading:
self.tree.heading("keywords", text="Keywords (AI)")
self.tree.column("keywords", width=200, minwidth=100)
```

**Step 4:** Modify MatterDialog._refresh_list to populate keywords

```python
# Import the format function at top of file:
from syncopaid.matter_client_dialog import get_matters_with_keywords

# In the method that populates treeview, use get_matters_with_keywords:
# Before:
# matters = self.db.get_matters()
# After:
matters = get_matters_with_keywords(self.db)

# When inserting into treeview, include keywords_display:
# Add m.get('keywords_display', '') to the values tuple
```

**Step 5 - Verify GREEN:**
```bash
pytest tests/test_matter_keywords.py::test_matter_dialog_has_keywords_column -v
```
Expected output: `PASSED`

**Step 6 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog_matters.py tests/test_matter_keywords.py && git commit -m "feat: add Keywords (AI) column to matter list dialog"
```

---

## Final Verification

Run after task completes:
```bash
python -m pytest tests/test_matter_keywords.py -v
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Keywords column is read-only - no edit functionality
- Column header "Keywords (AI)" clearly indicates AI management
- Uses existing format_keywords_for_display function from matter_client_dialog.py

## Next Task

After completion, execute sub-plan 023C2 for keyword tooltip functionality.
