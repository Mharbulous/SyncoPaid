# 014B: Activity-to-Matter Matching - Exact Matter Number

## Task
Implement exact matter number matching in window title with 100% confidence.

## Context
When a matter number appears exactly in the window title (e.g., "2024-001 - Contract.docx"), this is the highest confidence match possible.

## Scope
- Search for matter numbers in window title/url/path
- Return 100% confidence match
- Not flagged for review

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/categorizer.py` | Update categorize_activity() |
| `tests/test_categorizer.py` | Add test |

## Implementation

Update categorize_activity():

```python
# src/syncopaid/categorizer.py - in categorize_activity()
# Add after checking for empty matters:

# Combine all text for matching
search_text = " ".join(filter(None, [title, url, path])).lower()

# Strategy 1: Exact matter number match (highest confidence)
for matter in matters:
    matter_num = matter['matter_number']
    if matter_num.lower() in search_text:
        return CategorizationResult(
            matter_id=matter['id'],
            matter_number=matter_num,
            confidence=100,
            flagged_for_review=False,
            match_reason=f"Exact matter number '{matter_num}' found in window title"
        )

# No match found
return CategorizationResult(
    matter_id=None,
    matter_number=None,
    confidence=0,
    flagged_for_review=True,
    match_reason="No matching matter found"
)
```

### Test

```python
# tests/test_categorizer.py (add)
def test_exact_matter_number_match_in_title():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matter_id = db.insert_matter(
            matter_number="2024-001",
            description="Smith Contract Review"
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="2024-001 Smith Agreement v3.docx - Microsoft Word"
        )

        assert result.matter_id == matter_id
        assert result.matter_number == "2024-001"
        assert result.confidence == 100
        assert result.flagged_for_review is False
```

## Verification

```bash
pytest tests/test_categorizer.py::test_exact_matter_number_match_in_title -v
```

## Dependencies
- Task 014A (categorizer module)

## Next Task
After this: `014C_categorizer-client-keyword-matching.md`
