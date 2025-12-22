# 023C1: Matter Keywords - Format Functions

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add formatting functions for displaying keywords in the UI.
**Approach:** Create testable pure functions for keyword formatting before UI integration.
**Tech Stack:** Python (no tkinter required for this sub-plan)

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** Keywords displayed in matter list UI (read-only, AI-managed). Users see the keywords but cannot edit them - AI has complete control.

**Acceptance Criteria (partial):**
- [ ] Keywords formatting functions implemented

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023A complete (matter_keywords table exists)
- [ ] Sub-plan 023B complete (keyword extraction works)
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py tests/test_keyword_analyzer.py -v`

## TDD Tasks

### Task 1: Add keywords formatting functions (~5 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog.py`
- Test: `tests/test_matter_keywords.py`

**Context:** The MatterDialog class (in matter_client_dialog.py) displays matters in a tkinter treeview. We need to add formatting functions that convert keyword data to display strings.

**Step 1 - RED:** Write failing test
```python
# tests/test_matter_keywords.py (ADD to existing file)

def test_format_keywords_for_display():
    """Test formatting keywords for UI display."""
    from syncopaid.matter_client_dialog import format_keywords_for_display

    # Test with multiple keywords
    keywords = [
        {'keyword': 'smith', 'confidence': 0.95},
        {'keyword': 'contract', 'confidence': 0.80},
        {'keyword': 'litigation', 'confidence': 0.60},
    ]
    result = format_keywords_for_display(keywords)
    assert 'smith' in result
    assert 'contract' in result
    assert ', ' in result  # Comma separated

    # Test empty list
    assert format_keywords_for_display([]) == ""

    # Test max keywords (should truncate with ...)
    many_keywords = [{'keyword': f'kw{i}', 'confidence': 0.9} for i in range(10)]
    result = format_keywords_for_display(many_keywords, max_display=5)
    assert '...' in result


def test_get_matter_with_keywords():
    """Test that get_matters_with_keywords returns keyword data."""
    from syncopaid.matter_client_dialog import get_matters_with_keywords

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create matter with keywords
        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")
        db.add_matter_keyword(matter_id, "contract", source="ai", confidence=0.9)
        db.add_matter_keyword(matter_id, "smith", source="ai", confidence=0.8)

        matters = get_matters_with_keywords(db)
        assert len(matters) == 1
        assert matters[0]['matter_number'] == '2024-001'
        assert 'keywords_display' in matters[0]
        assert 'contract' in matters[0]['keywords_display']
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_matter_keywords.py::test_format_keywords_for_display -v
```
Expected output: `FAILED` (function does not exist)

**Step 3 - GREEN:** Add formatting functions
```python
# src/syncopaid/matter_client_dialog.py (ADD at top of file, after imports)

def format_keywords_for_display(
    keywords: list,
    max_display: int = 5
) -> str:
    """
    Format keywords list for UI display.

    Args:
        keywords: List of keyword dicts with 'keyword' and 'confidence'
        max_display: Maximum keywords to show before truncating

    Returns:
        Comma-separated string of keywords, with "..." if truncated
    """
    if not keywords:
        return ""

    # Sort by confidence (should already be sorted, but ensure)
    sorted_kw = sorted(keywords, key=lambda k: k.get('confidence', 0), reverse=True)

    # Take top N keywords
    display_kw = [k['keyword'] for k in sorted_kw[:max_display]]

    # Add ellipsis if truncated
    if len(sorted_kw) > max_display:
        display_kw.append("...")

    return ", ".join(display_kw)


def get_matters_with_keywords(db) -> list:
    """
    Get all matters with their AI-extracted keywords formatted for display.

    Args:
        db: Database instance

    Returns:
        List of matter dicts with added 'keywords_display' field
    """
    matters = db.get_matters(status='all')

    for matter in matters:
        keywords = db.get_matter_keywords(matter['id'])
        matter['keywords_display'] = format_keywords_for_display(keywords)
        matter['keywords_raw'] = keywords  # For tooltip/detail view

    return matters
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_matter_keywords.py::test_format_keywords_for_display tests/test_matter_keywords.py::test_get_matter_with_keywords -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog.py tests/test_matter_keywords.py && git commit -m "feat: add keyword formatting for matter list display"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_matter_keywords.py::test_format_keywords_for_display tests/test_matter_keywords.py::test_get_matter_with_keywords -v
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- These are pure functions that can be tested without GUI
- No tkinter required for this sub-plan
- Next sub-plan (023C2) will integrate these functions into the UI

## Next Sub-Plan

Continue with 023C2_matter-keywords-ui-column.md to add the Keywords column to the treeview.
