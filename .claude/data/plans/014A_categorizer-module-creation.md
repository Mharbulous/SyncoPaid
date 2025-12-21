# 014A: Activity-to-Matter Matching - Categorizer Module
Story ID: 8.4.1


## Task
Create the `categorizer.py` module with ActivityMatcher class and basic interface.

## Context
First step for automatic activity categorization. Creates the module structure and basic `categorize_activity()` method that returns "unknown" when no matters exist.

## Scope
- Create `src/syncopaid/categorizer.py`
- CategorizationResult dataclass
- ActivityMatcher class with db and confidence_threshold
- categorize_activity() returning unknown when no matters

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/categorizer.py` | New module (CREATE) |
| `tests/test_categorizer.py` | Create test file |

## Implementation

```python
# src/syncopaid/categorizer.py (CREATE)
"""Activity-to-matter categorization module."""
from dataclasses import dataclass
from typing import Optional, List, Dict
from .database import Database


@dataclass
class CategorizationResult:
    """Result of categorizing an activity."""
    matter_id: Optional[int]
    matter_number: Optional[str]
    confidence: int
    flagged_for_review: bool
    match_reason: str


class ActivityMatcher:
    """Matches activities to matters using keyword-based rules."""

    def __init__(self, db: Database, confidence_threshold: int = 70):
        self.db = db
        self.confidence_threshold = confidence_threshold

    def categorize_activity(
        self,
        app: Optional[str],
        title: Optional[str],
        url: Optional[str] = None,
        path: Optional[str] = None
    ) -> CategorizationResult:
        """Categorize an activity to the best-matching matter."""
        matters = self._get_active_matters()

        if not matters:
            return CategorizationResult(
                matter_id=None,
                matter_number=None,
                confidence=0,
                flagged_for_review=True,
                match_reason="No matters defined in database"
            )

        # Matching logic added in subsequent tasks
        return CategorizationResult(
            matter_id=None,
            matter_number=None,
            confidence=0,
            flagged_for_review=True,
            match_reason="No matching matter found"
        )

    def _get_active_matters(self) -> List[Dict]:
        """Get all active matters from database."""
        try:
            return self.db.get_matters(status='active')
        except Exception:
            return []
```

### Tests

```python
# tests/test_categorizer.py (CREATE)
"""Tests for activity-to-matter categorization."""
import pytest
import tempfile
from pathlib import Path
from syncopaid.database import Database
from syncopaid.categorizer import ActivityMatcher, CategorizationResult


def test_activity_matcher_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matcher = ActivityMatcher(db)
        assert matcher.db is db
        assert matcher.confidence_threshold == 70


def test_categorize_activity_returns_unknown_when_no_matters():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matcher = ActivityMatcher(db)

        result = matcher.categorize_activity(
            app="WINWORD.EXE", title="Document.docx"
        )

        assert result.matter_id is None
        assert result.confidence == 0
        assert result.flagged_for_review is True
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_categorizer.py -v
```

## Dependencies
- Story 8.1 (Matter/Client Database) should be implemented for full functionality

## Next Task
After this: `014B_categorizer-matter-number-matching.md`
