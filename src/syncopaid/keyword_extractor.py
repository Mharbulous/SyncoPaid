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
