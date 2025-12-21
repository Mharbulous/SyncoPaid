# 014C: Activity-to-Matter Matching - Client & Keyword Matching

## Task
Implement client name matching (80% confidence) and description keyword matching (60% confidence).

## Context
If exact matter number isn't found, try matching by client name or description keywords. These are lower confidence but still useful.

## Scope
- Client name match: 80% confidence
- Description keyword match: 60% confidence
- _extract_keywords() helper method

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/categorizer.py` | Add matching strategies |
| `tests/test_categorizer.py` | Add tests |

## Implementation

Add to categorize_activity() after matter number matching:

```python
# Strategy 2: Client name match (80% confidence)
for matter in matters:
    client_name = matter.get('client_name')
    if client_name and client_name.lower() in search_text:
        return CategorizationResult(
            matter_id=matter['id'],
            matter_number=matter['matter_number'],
            confidence=80,
            flagged_for_review=80 < self.confidence_threshold,
            match_reason=f"Client name '{client_name}' found in window title"
        )

# Strategy 3: Description keyword match (60% confidence)
for matter in matters:
    description = matter.get('description', '') or ''
    keywords = self._extract_keywords(description)

    matched_keywords = [kw for kw in keywords if kw.lower() in search_text]

    if matched_keywords:
        return CategorizationResult(
            matter_id=matter['id'],
            matter_number=matter['matter_number'],
            confidence=60,
            flagged_for_review=60 < self.confidence_threshold,
            match_reason=f"Keywords matched: {', '.join(matched_keywords)}"
        )
```

Add helper method:

```python
def _extract_keywords(self, text: str) -> List[str]:
    """Extract significant keywords from text."""
    import re

    stop_words = {
        'the', 'and', 'for', 'with', 'from', 'this', 'that',
        'are', 'was', 'were', 'been', 'have', 'has', 'had',
        'review', 'matter', 'file', 'document', 'project'
    }

    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if len(w) >= 3 and w not in stop_words]
```

### Tests

```python
# tests/test_categorizer.py (add)
def test_client_name_match_in_title():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        client_id = db.insert_client(name="Acme Corporation")
        matter_id = db.insert_matter(
            matter_number="2024-002", client_id=client_id
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="chrome.exe",
            title="Acme Corporation - Patent Search - Chrome"
        )

        assert result.matter_id == matter_id
        assert result.confidence == 80


def test_description_keyword_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matter_id = db.insert_matter(
            matter_number="2024-003",
            description="Employment Agreement Negotiation"
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="Employment Contract Template.docx"
        )

        assert result.matter_id == matter_id
        assert result.confidence == 60
        assert result.flagged_for_review is True  # 60 < 70 threshold
```

## Verification

```bash
pytest tests/test_categorizer.py -v
```

## Dependencies
- Task 014B (matter number matching)

## Next Task
After this: `014D_categorizer-database-schema.md`
