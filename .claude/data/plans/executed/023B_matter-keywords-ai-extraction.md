# 023B: Matter Keywords/Tags - AI Extraction Logic

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-21 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create AI logic to extract and rank keywords from matter activities.
**Approach:** Analyze activity titles/apps associated with a matter, extract meaningful keywords, filter common words, rank by uniqueness.
**Tech Stack:** Python stdlib (collections, re), no external NLP libraries needed for MVP

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** AI-powered keyword extraction ensures consistent quality and removes manual effort. AI identifies unique keywords per matter (case names, opposing counsel, court names) and filters out common/unreliable words.

**Acceptance Criteria:**
- [ ] AI analyzes activities associated with each matter and extracts frequently occurring keywords
- [ ] AI updates keywords automatically as new activities are categorized to matters
- [ ] AI identifies unique keywords per matter
- [ ] AI filters out common/unreliable words that don't help distinguish matters

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023A complete (matter_keywords table exists)
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Create keyword extractor module (~5 min)

**Files:**
- Create: `src/syncopaid/keyword_extractor.py`
- Test: `tests/test_keyword_extractor.py`

**Context:** We need a pure extraction module that takes activity text (window titles, app names) and returns candidate keywords. This module has no database dependencies - it's pure text processing.

**Step 1 - RED:** Write failing test
```python
# tests/test_keyword_extractor.py (CREATE)
"""Test keyword extraction from activity text."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syncopaid.keyword_extractor import KeywordExtractor


def test_extract_keywords_from_title():
    """Test basic keyword extraction from window title."""
    extractor = KeywordExtractor()
    keywords = extractor.extract("Smith v. Johnson - Contract Review.docx - Microsoft Word")

    # Should extract meaningful words, filter common ones
    assert "smith" in keywords
    assert "johnson" in keywords
    assert "contract" in keywords
    # Common words should be filtered
    assert "microsoft" not in keywords
    assert "word" not in keywords
    assert "docx" not in keywords


def test_extract_keywords_filters_stopwords():
    """Test that common stopwords are filtered."""
    extractor = KeywordExtractor()
    keywords = extractor.extract("The quick brown fox - Document.pdf")

    assert "quick" in keywords
    assert "brown" in keywords
    assert "fox" in keywords
    assert "the" not in keywords
    assert "pdf" not in keywords
    assert "document" not in keywords  # Too generic


def test_extract_keywords_handles_legal_terms():
    """Test extraction of legal-specific terms."""
    extractor = KeywordExtractor()
    keywords = extractor.extract("2024 BCSC 1234 - CanLII - Google Chrome")

    assert "bcsc" in keywords  # Court code
    assert "1234" in keywords  # Case number
    assert "canlii" in keywords  # Legal database
    assert "google" not in keywords
    assert "chrome" not in keywords


def test_extract_keywords_deduplicates():
    """Test that duplicate keywords are removed."""
    extractor = KeywordExtractor()
    keywords = extractor.extract("Smith Smith Smith Contract Contract")

    assert keywords.count("smith") == 1
    assert keywords.count("contract") == 1


if __name__ == "__main__":
    test_extract_keywords_from_title()
    test_extract_keywords_filters_stopwords()
    test_extract_keywords_handles_legal_terms()
    test_extract_keywords_deduplicates()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_keyword_extractor.py::test_extract_keywords_from_title -v
```
Expected output: `FAILED` (module does not exist)

**Step 3 - GREEN:** Create keyword extractor
```python
# src/syncopaid/keyword_extractor.py (CREATE)
"""
Keyword extraction from activity text for AI-powered matter matching.

Extracts meaningful keywords from window titles and app names while filtering
out common words, file extensions, and application names that don't help
distinguish between matters.
"""

import re
from typing import List, Set


class KeywordExtractor:
    """
    Extracts keywords from activity text for matter categorization.

    Uses stopword filtering, file extension removal, and app name filtering
    to identify meaningful keywords that help match activities to matters.
    """

    # Common English stopwords
    STOPWORDS: Set[str] = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'not', 'no', 'yes', 'all', 'each', 'every', 'both', 'few', 'more',
        'most', 'other', 'some', 'such', 'only', 'own', 'same', 'than',
        'too', 'very', 'just', 'also', 'now', 'new', 'one', 'two', 'first',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
    }

    # Common file extensions to filter
    FILE_EXTENSIONS: Set[str] = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
        'csv', 'html', 'htm', 'xml', 'json', 'png', 'jpg', 'jpeg', 'gif',
        'zip', 'rar', 'exe', 'dll', 'msg', 'eml',
    }

    # Common application names/terms to filter
    APP_NAMES: Set[str] = {
        'microsoft', 'word', 'excel', 'powerpoint', 'outlook', 'teams',
        'google', 'chrome', 'firefox', 'edge', 'safari', 'explorer',
        'adobe', 'acrobat', 'reader', 'notepad', 'visual', 'studio', 'code',
        'windows', 'file', 'folder', 'desktop', 'downloads', 'documents',
        'untitled', 'document', 'spreadsheet', 'presentation', 'draft',
    }

    # Minimum keyword length
    MIN_KEYWORD_LENGTH = 2

    def __init__(self):
        """Initialize the keyword extractor with combined filter set."""
        self._filter_words = (
            self.STOPWORDS |
            self.FILE_EXTENSIONS |
            self.APP_NAMES
        )

    def extract(self, text: str) -> List[str]:
        """
        Extract keywords from activity text.

        Args:
            text: Window title, app name, or combined activity text

        Returns:
            List of unique lowercase keywords, ordered by occurrence
        """
        if not text:
            return []

        # Normalize: lowercase, replace separators with spaces
        normalized = text.lower()
        normalized = re.sub(r'[-_./\\|:;,()]', ' ', normalized)

        # Split into words
        words = normalized.split()

        # Filter and deduplicate while preserving order
        seen = set()
        keywords = []

        for word in words:
            # Strip non-alphanumeric from edges
            word = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', word)

            # Skip if too short, filtered, or already seen
            if len(word) < self.MIN_KEYWORD_LENGTH:
                continue
            if word in self._filter_words:
                continue
            if word in seen:
                continue

            seen.add(word)
            keywords.append(word)

        return keywords

    def extract_with_frequency(self, texts: List[str]) -> List[tuple]:
        """
        Extract keywords from multiple texts with frequency counts.

        Args:
            texts: List of activity texts to analyze

        Returns:
            List of (keyword, count) tuples, sorted by frequency desc
        """
        from collections import Counter

        all_keywords = []
        for text in texts:
            all_keywords.extend(self.extract(text))

        counter = Counter(all_keywords)
        return counter.most_common()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_keyword_extractor.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/keyword_extractor.py tests/test_keyword_extractor.py && git commit -m "feat: add keyword extractor for activity text analysis"
```

---

### Task 2: Add frequency-based keyword ranking (~4 min)

**Files:**
- Modify: `src/syncopaid/keyword_extractor.py`
- Test: `tests/test_keyword_extractor.py`

**Context:** AI needs to rank keywords by how frequently they appear in a matter's activities and how unique they are across all matters. More frequent = more relevant to this matter.

**Step 1 - RED:** Write failing test
```python
# tests/test_keyword_extractor.py (ADD to existing file)

def test_extract_with_frequency():
    """Test keyword frequency counting across multiple texts."""
    extractor = KeywordExtractor()

    texts = [
        "Smith v. Johnson - Contract Draft",
        "Smith v. Johnson - Contract Review",
        "Smith v. Johnson - Research Notes",
        "Unrelated Document - Other Matter",
    ]

    ranked = extractor.extract_with_frequency(texts)

    # Convert to dict for easier testing
    freq_dict = dict(ranked)

    # Smith and Johnson should appear 3 times each
    assert freq_dict.get("smith") == 3
    assert freq_dict.get("johnson") == 3
    # Contract appears twice
    assert freq_dict.get("contract") == 2
    # Other terms appear once
    assert freq_dict.get("research") == 1


def test_calculate_keyword_confidence():
    """Test confidence score calculation based on frequency."""
    extractor = KeywordExtractor()

    texts = [
        "Smith Contract Review",
        "Smith Contract Draft",
        "Smith Meeting Notes",
        "Johnson Unrelated",
    ]

    scored = extractor.calculate_confidence(texts, top_n=5)

    # Smith appears most (3/4 = 0.75), should have highest confidence
    smith_score = next((s for k, s in scored if k == "smith"), None)
    assert smith_score is not None
    assert smith_score >= 0.7

    # Contract appears 2/4 = 0.5
    contract_score = next((s for k, s in scored if k == "contract"), None)
    assert contract_score is not None
    assert contract_score >= 0.4


if __name__ == "__main__":
    test_extract_keywords_from_title()
    test_extract_keywords_filters_stopwords()
    test_extract_keywords_handles_legal_terms()
    test_extract_keywords_deduplicates()
    test_extract_with_frequency()
    test_calculate_keyword_confidence()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_keyword_extractor.py::test_calculate_keyword_confidence -v
```
Expected output: `FAILED` (method does not exist)

**Step 3 - GREEN:** Add confidence calculation
```python
# src/syncopaid/keyword_extractor.py (ADD after extract_with_frequency method)

    def calculate_confidence(
        self,
        texts: List[str],
        top_n: int = 10
    ) -> List[tuple]:
        """
        Calculate confidence scores for keywords based on frequency.

        Confidence = (times keyword appears) / (total number of texts)
        This gives a 0.0-1.0 score representing how consistently
        this keyword appears in the matter's activities.

        Args:
            texts: List of activity texts for a single matter
            top_n: Maximum number of keywords to return

        Returns:
            List of (keyword, confidence) tuples, sorted by confidence desc
        """
        if not texts:
            return []

        frequency = self.extract_with_frequency(texts)
        total_texts = len(texts)

        scored = []
        for keyword, count in frequency[:top_n * 2]:  # Get extra, filter later
            confidence = round(count / total_texts, 2)
            # Only include keywords that appear in at least 20% of activities
            if confidence >= 0.2:
                scored.append((keyword, confidence))

        return scored[:top_n]
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_keyword_extractor.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/keyword_extractor.py tests/test_keyword_extractor.py && git commit -m "feat: add confidence scoring for keyword extraction"
```

---

### Task 3: Create matter keyword analyzer service (~5 min)

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

- KeywordExtractor is pure text processing - no database dependencies
- MatterKeywordAnalyzer coordinates between database and extractor
- Keywords are always lowercase for consistent matching
- Confidence threshold of 0.2 filters out keywords appearing in less than 20% of activities
- Future enhancement: query events table for activities assigned to a matter (requires events.matter column from story 8.1.2)

## Dependencies

- Sub-plan 023A must be complete (matter_keywords table exists)

## Next Task

After this: `023C_matter-keywords-ui-display.md`
