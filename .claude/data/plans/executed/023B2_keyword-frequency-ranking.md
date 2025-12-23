# 023B2: Keyword Frequency-Based Ranking

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add frequency-based keyword ranking with confidence scores.
**Approach:** Extend KeywordExtractor with calculate_confidence method that ranks keywords by how frequently they appear across activities.
**Tech Stack:** Python stdlib (collections), no external dependencies

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** AI-powered keyword extraction ensures consistent quality and removes manual effort. AI identifies unique keywords per matter (case names, opposing counsel, court names) and filters out common/unreliable words.

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023B1 complete (KeywordExtractor class exists with extract and extract_with_frequency methods)
- [ ] Tests pass: `python -m pytest tests/test_keyword_extractor.py -v`

## TDD Tasks

### Task 1: Add frequency-based keyword ranking (~4 min)

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_keyword_extractor.py -v
python -c "from syncopaid.keyword_extractor import KeywordExtractor; e = KeywordExtractor(); print(e.calculate_confidence(['test one', 'test two']))"
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Confidence score = frequency / total_texts (0.0 to 1.0)
- Minimum threshold of 0.2 filters keywords appearing in less than 20% of activities
- top_n parameter limits output to most confident keywords

## Next Task

After this: `023B3_matter-keyword-analyzer.md`
