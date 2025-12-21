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
