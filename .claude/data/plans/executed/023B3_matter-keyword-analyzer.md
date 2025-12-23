# 023B3: Matter Keyword Analyzer Service

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create matter keyword analyzer service that ties together database and extractor.
**Approach:** Build MatterKeywordAnalyzer class that queries activities, extracts keywords, and updates the database.
**Tech Stack:** Python stdlib, uses KeywordExtractor and Database classes

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** AI-powered keyword extraction ensures consistent quality and removes manual effort. AI identifies unique keywords per matter (case names, opposing counsel, court names) and filters out common/unreliable words.

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023A complete (matter_keywords table exists with CRUD operations)
- [ ] Sub-plan 023B1 complete (KeywordExtractor class exists)
- [ ] Sub-plan 023B2 complete (calculate_confidence method exists)
- [ ] Tests pass: `python -m pytest tests/test_keyword_extractor.py tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Create matter keyword analyzer service (~5 min)

**Files:**
- Create: `src/syncopaid/keyword_analyzer.py`
- Test: `tests/test_keyword_analyzer.py`

**Context:** This service ties together the database and extractor. It queries activities for a matter, extracts keywords, and updates the database. This is what gets called when AI updates keywords.

**Step 1 - RED:** Write failing test
```python
# tests/test_keyword_analyzer.py (CREATE)
"""Test matter keyword analyzer service."""
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syncopaid.database import Database
from syncopaid.keyword_analyzer import MatterKeywordAnalyzer


def test_analyze_matter_keywords():
    """Test analyzing and storing keywords for a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create matter with some activities
        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Smith v. Johnson")

        # Simulate activities (insert with window titles)
        from syncopaid.tracker import ActivityEvent
        events = [
            ActivityEvent(
                timestamp="2025-12-21T10:00:00",
                duration_seconds=300,
                app="WINWORD.EXE",
                title="Smith v. Johnson - Contract Draft.docx - Word",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-21T10:05:00",
                duration_seconds=600,
                app="chrome.exe",
                title="Smith v. Johnson case law - Google Chrome",
                is_idle=False
            ),
        ]
        db.insert_events_batch(events)

        # For this test, we'll simulate events being assigned to the matter
        # by analyzing the matter description + simulated titles

        analyzer = MatterKeywordAnalyzer(db)
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Smith v. Johnson - Contract Draft.docx",
            "Smith v. Johnson case law research",
            "Smith v. Johnson - Motion to Dismiss",
        ])

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) > 0

        keyword_texts = [k['keyword'] for k in keywords]
        assert 'smith' in keyword_texts
        assert 'johnson' in keyword_texts


def test_analyze_matter_updates_existing():
    """Test that re-analysis updates keywords, not duplicates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        analyzer = MatterKeywordAnalyzer(db)

        # First analysis
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Contract review meeting",
            "Contract drafting session",
        ])
        initial_keywords = db.get_matter_keywords(matter_id)

        # Second analysis with different activities
        analyzer.analyze_matter(matter_id, activity_titles=[
            "Litigation strategy discussion",
            "Court filing preparation",
        ])
        updated_keywords = db.get_matter_keywords(matter_id)

        # Should have replaced keywords, not accumulated
        keyword_texts = [k['keyword'] for k in updated_keywords]
        assert 'litigation' in keyword_texts or 'court' in keyword_texts
        # Old keywords should be gone
        assert 'contract' not in keyword_texts


if __name__ == "__main__":
    test_analyze_matter_keywords()
    test_analyze_matter_updates_existing()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_keyword_analyzer.py::test_analyze_matter_keywords -v
```
Expected output: `FAILED` (module does not exist)

**Step 3 - GREEN:** Create analyzer service
```python
# src/syncopaid/keyword_analyzer.py (CREATE)
"""
Matter keyword analyzer service.

Analyzes activities for a matter and extracts AI-managed keywords.
This service coordinates between the database and keyword extractor.
"""

import logging
from typing import List, Optional

from .keyword_extractor import KeywordExtractor


class MatterKeywordAnalyzer:
    """
    Analyzes matter activities and extracts keywords.

    Provides the AI interface for keyword extraction and storage.
    Keywords are fully managed by this service - users cannot edit directly.
    """

    def __init__(self, database):
        """
        Initialize the analyzer with database connection.

        Args:
            database: Database instance with keyword methods
        """
        self.db = database
        self.extractor = KeywordExtractor()

    def analyze_matter(
        self,
        matter_id: int,
        activity_titles: Optional[List[str]] = None,
        top_n: int = 10
    ) -> int:
        """
        Analyze activities for a matter and update keywords.

        If activity_titles is not provided, queries the database for
        events assigned to this matter (future enhancement).

        Args:
            matter_id: ID of the matter to analyze
            activity_titles: List of window titles/activity descriptions
            top_n: Maximum number of keywords to store

        Returns:
            Number of keywords stored
        """
        if not activity_titles:
            # Future: query events table for activities assigned to this matter
            # For now, require titles to be provided
            logging.warning(f"No activity titles provided for matter {matter_id}")
            return 0

        # Extract keywords with confidence scores
        scored_keywords = self.extractor.calculate_confidence(
            activity_titles,
            top_n=top_n
        )

        if not scored_keywords:
            logging.info(f"No keywords extracted for matter {matter_id}")
            return 0

        # Convert to format expected by database
        keywords = [
            {"keyword": kw, "confidence": conf}
            for kw, conf in scored_keywords
        ]

        # Update database (replaces existing AI keywords)
        count = self.db.update_matter_keywords(
            matter_id,
            keywords,
            source="ai"
        )

        logging.info(f"Updated {count} keywords for matter {matter_id}")
        return count

    def analyze_all_matters(self) -> dict:
        """
        Analyze all active matters and update their keywords.

        Returns:
            Dict with matter_id -> keyword_count mappings
        """
        results = {}
        matters = self.db.get_matters(status='active')

        for matter in matters:
            # Future: get activities assigned to this matter
            # For now, skip matters without assigned activities
            results[matter['id']] = 0

        return results
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_keyword_analyzer.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/keyword_analyzer.py tests/test_keyword_analyzer.py && git commit -m "feat: add matter keyword analyzer service for AI keyword extraction"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_keyword_extractor.py tests/test_keyword_analyzer.py tests/test_matter_keywords.py -v
python -c "from syncopaid.keyword_analyzer import MatterKeywordAnalyzer; print('OK')"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- MatterKeywordAnalyzer coordinates between database and extractor
- Keywords are always lowercase for consistent matching
- Confidence threshold of 0.2 filters out keywords appearing in less than 20% of activities
- Future enhancement: query events table for activities assigned to a matter (requires events.matter column from story 8.1.2)

## Next Task

After this: `023C_matter-keywords-ui-display.md`
