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

        # Combine all text for matching
        search_text = " ".join(filter(None, [title, url, path])).lower()

        # Strategy 1: Exact matter number match (highest confidence)
        for matter in matters:
            matter_num = matter['matter_number']
            if matter_num.lower() in search_text:
                return CategorizationResult(
                    matter_id=matter['id'],
                    matter_number=matter_num,
                    confidence=100,
                    flagged_for_review=False,
                    match_reason=f"Exact matter number '{matter_num}' found in window title"
                )

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

        # No match found
        return CategorizationResult(
            matter_id=None,
            matter_number=None,
            confidence=0,
            flagged_for_review=True,
            match_reason="No matching matter found"
        )

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

    def _get_active_matters(self) -> List[Dict]:
        """Get all active matters from database."""
        try:
            return self.db.get_matters(status='active')
        except Exception:
            return []
