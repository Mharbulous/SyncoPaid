# 023B1: Keyword Extractor Module

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create pure keyword extraction module for activity text analysis.
**Approach:** Build a KeywordExtractor class that extracts meaningful keywords from window titles/app names while filtering stopwords, file extensions, and application names.
**Tech Stack:** Python stdlib (re), no external dependencies

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** AI-powered keyword extraction ensures consistent quality and removes manual effort. AI identifies unique keywords per matter (case names, opposing counsel, court names) and filters out common/unreliable words.

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_keyword_extractor.py -v
python -c "from syncopaid.keyword_extractor import KeywordExtractor; print('OK')"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- KeywordExtractor is pure text processing - no database dependencies
- Keywords are always lowercase for consistent matching
- extract_with_frequency is included for use by Task 2

## Next Task

After this: `023B2_keyword-frequency-ranking.md`
