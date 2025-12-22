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
