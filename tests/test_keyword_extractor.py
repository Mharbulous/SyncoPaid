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
