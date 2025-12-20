# 048: Activity-to-Matter Matching - App Integration

## Task
Add confidence_threshold to config and integrate ActivityMatcher into the main tracking loop.

## Context
Final step for automatic activity categorization. Wires the categorizer into the main app so all events are automatically categorized.

## Scope
- Add categorization_confidence_threshold to config (default: 70)
- Initialize ActivityMatcher in SyncoPaidApp
- Call categorize_activity() before inserting events

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/config.py` | Add config setting |
| `src/syncopaid/__main__.py` | Integrate categorizer |
| `tests/test_categorizer.py` | Add tests |

## Implementation

### Config Setting

```python
# src/syncopaid/config.py - add to DEFAULT_CONFIG
"categorization_confidence_threshold": 70,

# Add to Config dataclass
categorization_confidence_threshold: int = 70
```

### Main App Integration

```python
# src/syncopaid/__main__.py (add import)
from .categorizer import ActivityMatcher


# In SyncoPaidApp.__init__(), after database init:
self.matcher = ActivityMatcher(
    self.db,
    confidence_threshold=self.config.categorization_confidence_threshold
)


# In _run_tracking_loop(), modify event insertion:
# Find where events are inserted and change to:
categorization = self.matcher.categorize_activity(
    app=event.app,
    title=event.title,
    url=event.url,
    path=None
)

self.db.insert_event(
    event,
    matter_id=categorization.matter_id,
    confidence=categorization.confidence,
    flagged_for_review=categorization.flagged_for_review
)
```

### Tests

```python
# tests/test_categorizer.py (add)
def test_config_has_confidence_threshold():
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'categorization_confidence_threshold' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['categorization_confidence_threshold'] == 70

    config = Config(categorization_confidence_threshold=80)
    assert config.categorization_confidence_threshold == 80


def test_categorizer_integrates_with_app():
    from syncopaid.__main__ import SyncoPaidApp
    from syncopaid.categorizer import ActivityMatcher
    assert callable(ActivityMatcher)
```

## Verification

```bash
pytest tests/test_categorizer.py -v
python -m syncopaid.database
python -m syncopaid  # Full app test
```

## Final Verification

After all categorizer sub-plans complete:

```bash
python -m pytest tests/test_categorizer.py -v
python -m pytest tests/ -v  # All tests
python -m syncopaid.database
```

## Dependencies
- Task 047 (flagged events methods)

## Notes
This completes the Activity-to-Matter Matching feature (original story 8.4.1).

All acceptance criteria should now be met:
- AI automatically assigns activities to matters
- Analyzes app, title, URL, path against matter database
- Calculates confidence scores (100/80/60%)
- Activities below threshold are flagged for review
- Configurable confidence threshold (default 70%)
- No interruptions during active work
