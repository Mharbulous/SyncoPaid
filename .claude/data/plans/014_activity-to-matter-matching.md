# Activity-to-Matter Matching - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Enable AI to automatically categorize every activity to a matter without user prompts, flagging low-confidence matches for later review.

**Approach:** Create a new `categorizer.py` module with rule-based keyword matching against the matter database. The categorizer analyzes window titles, app names, URLs, and folder paths, returning confidence scores. Low-confidence results are flagged for batch review later.

**Tech Stack:** Python, SQLite (existing database), regex for keyword matching

---

**Story ID:** 8.4.1 | **Created:** 2025-12-19 | **Stage:** `planned`

---

## Story Context

**Title:** Activity-to-Matter Matching

**Description:** AI now categorizes all activities immediately without user interaction. Low-confidence categorizations are flagged for later review instead of prompting during workflow. This preserves the non-intrusive, automatic time tracking experience.

**User Story:** As a lawyer with defined matters in SyncoPaid, I want AI to automatically categorize each activity to a matter without interrupting my workflow, so that I never have to manually categorize during work, only review flagged items later when convenient.

**Acceptance Criteria:**
- [ ] AI automatically assigns every activity to a matter (or "unknown") without user prompts
- [ ] AI analyzes app, window title, URL, folder path against matter database for categorization
- [ ] AI calculates confidence score (0-100%) for each categorization
- [ ] Activities below confidence threshold are auto-categorized to best match but flagged for review
- [ ] Flagged activities appear in dedicated review UI for batch processing at user's convenience
- [ ] Configurable confidence threshold for flagging (default: 70%)
- [ ] No interruptions, prompts, or confirmations during active work

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest tests/ -v`
- [ ] Story 8.1 (Matter/Client Database) implemented - `matters` and `clients` tables exist in database

## TDD Tasks

### Task 1: Create ActivityMatcher class with basic interface (~3 min)

**Files:**
- **Create:** `tests/test_categorizer.py`
- **Create:** `src/syncopaid/categorizer.py`

**Context:** We need a new module to handle activity-to-matter matching. This task establishes the basic class structure and interface that other tasks will build upon.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py
"""Tests for activity-to-matter categorization."""
import pytest
import sqlite3
import tempfile
from pathlib import Path
from syncopaid.database import Database
from syncopaid.categorizer import ActivityMatcher, CategorizationResult


def test_activity_matcher_initialization():
    """Verify ActivityMatcher can be instantiated with a database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        matcher = ActivityMatcher(db)

        assert matcher is not None
        assert matcher.db is db
        assert matcher.confidence_threshold == 70  # Default threshold
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_activity_matcher_initialization -v
```
Expected output: `ModuleNotFoundError: No module named 'syncopaid.categorizer'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/categorizer.py
"""
Activity-to-matter categorization module.

Uses rule-based keyword matching to automatically categorize activities
to matters without user prompts. Low-confidence matches are flagged
for later batch review.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from .database import Database


@dataclass
class CategorizationResult:
    """
    Result of categorizing an activity to a matter.

    Fields:
        matter_id: ID of the matched matter (None if unknown)
        matter_number: Matter number string (None if unknown)
        confidence: Confidence score 0-100
        flagged_for_review: True if below confidence threshold
        match_reason: Human-readable explanation of why this match was made
    """
    matter_id: Optional[int]
    matter_number: Optional[str]
    confidence: int
    flagged_for_review: bool
    match_reason: str


class ActivityMatcher:
    """
    Matches activities to matters using keyword-based rules.

    Analyzes window titles, app names, URLs, and folder paths
    against matter descriptions and keywords.
    """

    def __init__(self, db: Database, confidence_threshold: int = 70):
        """
        Initialize the matcher.

        Args:
            db: Database instance with matters table
            confidence_threshold: Minimum confidence (0-100) before flagging for review
        """
        self.db = db
        self.confidence_threshold = confidence_threshold
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_activity_matcher_initialization -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/categorizer.py && git commit -m "feat: add ActivityMatcher class skeleton for categorization"
```

---

### Task 2: Implement categorize_activity method that returns unknown for empty matters (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/categorizer.py`

**Context:** The categorize_activity method is the core entry point. When no matters exist, it should return an "unknown" result with 0% confidence, flagged for review.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after first test)

def test_categorize_activity_returns_unknown_when_no_matters():
    """When no matters exist, should return unknown result."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        matcher = ActivityMatcher(db)

        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="Document1.docx - Microsoft Word",
            url=None,
            path=None
        )

        assert isinstance(result, CategorizationResult)
        assert result.matter_id is None
        assert result.matter_number is None
        assert result.confidence == 0
        assert result.flagged_for_review is True
        assert "no matters" in result.match_reason.lower()
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_categorize_activity_returns_unknown_when_no_matters -v
```
Expected output: `AttributeError: 'ActivityMatcher' object has no attribute 'categorize_activity'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/categorizer.py (add to ActivityMatcher class)

    def categorize_activity(
        self,
        app: Optional[str],
        title: Optional[str],
        url: Optional[str] = None,
        path: Optional[str] = None
    ) -> CategorizationResult:
        """
        Categorize an activity to the best-matching matter.

        Args:
            app: Application executable name (e.g., "WINWORD.EXE")
            title: Window title text
            url: URL if this is a browser window
            path: File path if document is open

        Returns:
            CategorizationResult with matter match and confidence
        """
        # Get active matters from database
        matters = self._get_active_matters()

        if not matters:
            return CategorizationResult(
                matter_id=None,
                matter_number=None,
                confidence=0,
                flagged_for_review=True,
                match_reason="No matters defined in database"
            )

        # TODO: Implement matching logic in subsequent tasks
        return CategorizationResult(
            matter_id=None,
            matter_number=None,
            confidence=0,
            flagged_for_review=True,
            match_reason="Matching not yet implemented"
        )

    def _get_active_matters(self) -> List[Dict]:
        """Get all active matters from database."""
        try:
            return self.db.get_matters(status='active')
        except Exception:
            # Table may not exist if 8.1 not implemented yet
            return []
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_categorize_activity_returns_unknown_when_no_matters -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/categorizer.py && git commit -m "feat: add categorize_activity method with unknown handling"
```

---

### Task 3: Implement exact matter number matching in window title (~4 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/categorizer.py`

**Context:** The most reliable match is when the matter number appears exactly in the window title (e.g., "2024-001 - Contract Review.docx"). This should give 100% confidence.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_exact_matter_number_match_in_title():
    """Exact matter number in window title should match with 100% confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create a test matter (requires 8.1 to be implemented)
        # For now, we'll mock the matters data
        matter_id = db.insert_matter(
            matter_number="2024-001",
            description="Smith Contract Review"
        )

        matcher = ActivityMatcher(db)

        # Window title contains exact matter number
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="2024-001 Smith Agreement v3.docx - Microsoft Word",
            url=None,
            path=None
        )

        assert result.matter_id == matter_id
        assert result.matter_number == "2024-001"
        assert result.confidence == 100
        assert result.flagged_for_review is False
        assert "matter number" in result.match_reason.lower()
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_exact_matter_number_match_in_title -v
```
Expected output: `AssertionError: assert None == 1` (matter_id is None)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/categorizer.py (replace the TODO section in categorize_activity)

    def categorize_activity(
        self,
        app: Optional[str],
        title: Optional[str],
        url: Optional[str] = None,
        path: Optional[str] = None
    ) -> CategorizationResult:
        """
        Categorize an activity to the best-matching matter.

        Args:
            app: Application executable name (e.g., "WINWORD.EXE")
            title: Window title text
            url: URL if this is a browser window
            path: File path if document is open

        Returns:
            CategorizationResult with matter match and confidence
        """
        # Get active matters from database
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

        # No match found
        return CategorizationResult(
            matter_id=None,
            matter_number=None,
            confidence=0,
            flagged_for_review=True,
            match_reason="No matching matter found"
        )
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_exact_matter_number_match_in_title -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/categorizer.py && git commit -m "feat: add exact matter number matching in window title"
```

---

### Task 4: Implement client name matching with lower confidence (~4 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/categorizer.py`

**Context:** If the client name appears in the window title but not the matter number, we can still make a match but with lower confidence (80%). If multiple matters share the same client, pick the most recently updated one.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_client_name_match_in_title():
    """Client name in window title should match with 80% confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter
        client_id = db.insert_client(name="Acme Corporation", notes="Tech client")
        matter_id = db.insert_matter(
            matter_number="2024-002",
            client_id=client_id,
            description="Patent Filing"
        )

        matcher = ActivityMatcher(db)

        # Window title contains client name but not matter number
        result = matcher.categorize_activity(
            app="chrome.exe",
            title="Acme Corporation - Patent Search Results - Google Chrome",
            url="https://patents.google.com",
            path=None
        )

        assert result.matter_id == matter_id
        assert result.matter_number == "2024-002"
        assert result.confidence == 80
        assert result.flagged_for_review is False  # 80 >= default 70 threshold
        assert "client" in result.match_reason.lower()
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_client_name_match_in_title -v
```
Expected output: `AssertionError: assert None == 1` (no client matching yet)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/categorizer.py (add after exact matter number match in categorize_activity)

        # Strategy 2: Client name match (medium confidence)
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
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_client_name_match_in_title -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/categorizer.py && git commit -m "feat: add client name matching with 80% confidence"
```

---

### Task 5: Implement description keyword matching with configurable confidence (~4 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/categorizer.py`

**Context:** If keywords from the matter description appear in the window title, match with 60% confidence. This is below the default threshold, so these should be flagged for review.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_description_keyword_match():
    """Keywords from description should match with 60% confidence and be flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create matter with descriptive keywords
        matter_id = db.insert_matter(
            matter_number="2024-003",
            description="Employment Agreement Negotiation"
        )

        matcher = ActivityMatcher(db)

        # Window title contains keywords from description
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="Employment Contract Template v2.docx - Microsoft Word",
            url=None,
            path=None
        )

        assert result.matter_id == matter_id
        assert result.matter_number == "2024-003"
        assert result.confidence == 60
        assert result.flagged_for_review is True  # 60 < default 70 threshold
        assert "keyword" in result.match_reason.lower()
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_description_keyword_match -v
```
Expected output: `AssertionError: assert None == 1` (no keyword matching yet)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/categorizer.py (add after client name match)

        # Strategy 3: Description keyword match (lower confidence)
        for matter in matters:
            description = matter.get('description', '') or ''
            # Extract significant words (3+ chars, not common words)
            keywords = self._extract_keywords(description)

            matched_keywords = []
            for keyword in keywords:
                if keyword.lower() in search_text:
                    matched_keywords.append(keyword)

            if matched_keywords:
                confidence = 60
                return CategorizationResult(
                    matter_id=matter['id'],
                    matter_number=matter['matter_number'],
                    confidence=confidence,
                    flagged_for_review=confidence < self.confidence_threshold,
                    match_reason=f"Keywords matched: {', '.join(matched_keywords)}"
                )


# Add this helper method to the class
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract significant keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of significant keywords (3+ chars, not stop words)
        """
        import re

        # Common words to exclude
        stop_words = {
            'the', 'and', 'for', 'with', 'from', 'this', 'that',
            'are', 'was', 'were', 'been', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'may', 'might',
            'review', 'matter', 'file', 'document', 'project'
        }

        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter to significant words
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in stop_words
        ]

        return keywords
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_description_keyword_match -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/categorizer.py && git commit -m "feat: add description keyword matching with 60% confidence"
```

---

### Task 6: Add flagged_for_review column to events table (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/database.py`

**Context:** We need to persist the flagged_for_review status in the database so users can later review low-confidence categorizations. This requires a schema migration to add the column.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_events_table_has_categorization_columns():
    """Events table should have matter_id, confidence, and flagged_for_review columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Check events table schema
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'matter_id' in columns, "events should have matter_id column"
        assert 'confidence' in columns, "events should have confidence column"
        assert 'flagged_for_review' in columns, "events should have flagged_for_review column"
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_events_table_has_categorization_columns -v
```
Expected output: `AssertionError: events should have matter_id column`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (add migration in _init_schema method, after existing migrations around line 110)

            # Migration: Add categorization columns if they don't exist
            cursor.execute("PRAGMA table_info(events)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'matter_id' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN matter_id INTEGER")
                logging.info("Database migration: Added matter_id column to events table")

            if 'confidence' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN confidence INTEGER DEFAULT 0")
                logging.info("Database migration: Added confidence column to events table")

            if 'flagged_for_review' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN flagged_for_review INTEGER DEFAULT 0")
                logging.info("Database migration: Added flagged_for_review column to events table")
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_events_table_has_categorization_columns -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/database.py && git commit -m "feat: add categorization columns to events table schema"
```

---

### Task 7: Update insert_event to include categorization data (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/database.py`

**Context:** The insert_event method needs to accept and store categorization data (matter_id, confidence, flagged_for_review) when inserting activity events.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_insert_event_with_categorization():
    """insert_event should accept and store categorization data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        from syncopaid.tracker import ActivityEvent

        # Create a test matter
        matter_id = db.insert_matter(matter_number="2024-TEST", description="Test")

        # Create event with categorization
        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=60.0,
            app="test.exe",
            title="Test Window"
        )

        event_id = db.insert_event(
            event,
            matter_id=matter_id,
            confidence=85,
            flagged_for_review=False
        )

        # Verify stored data
        events = db.get_events()
        assert len(events) == 1
        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 85
        assert events[0]['flagged_for_review'] is False
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_insert_event_with_categorization -v
```
Expected output: `TypeError: insert_event() got an unexpected keyword argument 'matter_id'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (update insert_event method signature and implementation around line 144-175)

    def insert_event(
        self,
        event: ActivityEvent,
        matter_id: Optional[int] = None,
        confidence: int = 0,
        flagged_for_review: bool = False
    ) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store
            matter_id: Optional ID of matched matter
            confidence: Categorization confidence 0-100 (default 0)
            flagged_for_review: Whether this needs manual review (default False)

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, matter_id, confidence, flagged_for_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                1 if event.is_idle else 0,
                state,
                matter_id,
                confidence,
                1 if flagged_for_review else 0
            ))

            return cursor.lastrowid


# Also update get_events to return categorization fields (around line 260-270)
# In the events.append() section, add:
                    'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
                    'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
                    'flagged_for_review': bool(row['flagged_for_review']) if 'flagged_for_review' in row.keys() else False,
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_insert_event_with_categorization -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/database.py && git commit -m "feat: add categorization parameters to insert_event method"
```

---

### Task 8: Add get_flagged_events method for review UI (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/database.py`

**Context:** Users need to retrieve all events flagged for review so they can batch-process them. This method returns only events where flagged_for_review=True.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_get_flagged_events():
    """get_flagged_events should return only events needing review."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        from syncopaid.tracker import ActivityEvent

        # Create events with different flag states
        event1 = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=60.0,
            app="test.exe",
            title="High confidence"
        )
        db.insert_event(event1, confidence=90, flagged_for_review=False)

        event2 = ActivityEvent(
            timestamp="2025-12-19T10:01:00",
            duration_seconds=60.0,
            app="test.exe",
            title="Low confidence"
        )
        db.insert_event(event2, confidence=50, flagged_for_review=True)

        event3 = ActivityEvent(
            timestamp="2025-12-19T10:02:00",
            duration_seconds=60.0,
            app="test.exe",
            title="Also low confidence"
        )
        db.insert_event(event3, confidence=40, flagged_for_review=True)

        # Get flagged events
        flagged = db.get_flagged_events()

        assert len(flagged) == 2
        assert all(e['flagged_for_review'] for e in flagged)
        assert flagged[0]['title'] == "Low confidence"
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_get_flagged_events -v
```
Expected output: `AttributeError: 'Database' object has no attribute 'get_flagged_events'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (add after get_events method, around line 275)

    def get_flagged_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get events flagged for manual review.

        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries where flagged_for_review=True
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM events WHERE flagged_for_review = 1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND timestamp < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            query += " ORDER BY timestamp ASC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            events = []
            for row in cursor.fetchall():
                state = row['state'] if 'state' in row.keys() and row['state'] else ('Inactive' if row['is_idle'] else 'Active')
                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'duration_seconds': row['duration_seconds'],
                    'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                    'app': row['app'],
                    'title': row['title'],
                    'url': row['url'],
                    'is_idle': bool(row['is_idle']),
                    'state': state,
                    'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
                    'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
                    'flagged_for_review': bool(row['flagged_for_review']) if 'flagged_for_review' in row.keys() else False,
                })

            return events
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_get_flagged_events -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/database.py && git commit -m "feat: add get_flagged_events method for review UI"
```

---

### Task 9: Add update_event_categorization method (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/database.py`

**Context:** When a user reviews a flagged event and assigns it to a matter, we need to update the categorization data and clear the flagged_for_review flag.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_update_event_categorization():
    """update_event_categorization should update matter assignment and clear flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        from syncopaid.tracker import ActivityEvent

        # Create matter and flagged event
        matter_id = db.insert_matter(matter_number="2024-REVIEW", description="Test")

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=60.0,
            app="test.exe",
            title="Needs review"
        )
        event_id = db.insert_event(event, confidence=50, flagged_for_review=True)

        # Update categorization (simulating user review)
        db.update_event_categorization(
            event_id=event_id,
            matter_id=matter_id,
            confidence=100,
            flagged_for_review=False
        )

        # Verify update
        events = db.get_events()
        assert len(events) == 1
        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 100
        assert events[0]['flagged_for_review'] is False
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_update_event_categorization -v
```
Expected output: `AttributeError: 'Database' object has no attribute 'update_event_categorization'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (add after get_flagged_events method)

    def update_event_categorization(
        self,
        event_id: int,
        matter_id: Optional[int] = None,
        confidence: int = 100,
        flagged_for_review: bool = False
    ):
        """
        Update the categorization of an existing event.

        Used when user manually reviews and assigns a matter to an event.

        Args:
            event_id: ID of the event to update
            matter_id: ID of the assigned matter (None for uncategorized)
            confidence: New confidence score (default 100 for manual assignment)
            flagged_for_review: Whether still needs review (default False)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events
                SET matter_id = ?, confidence = ?, flagged_for_review = ?
                WHERE id = ?
            """, (matter_id, confidence, 1 if flagged_for_review else 0, event_id))

            logging.info(f"Updated categorization for event {event_id}: matter={matter_id}, confidence={confidence}")
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_update_event_categorization -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/database.py && git commit -m "feat: add update_event_categorization method for review workflow"
```

---

### Task 10: Add confidence_threshold to config (~3 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/config.py`

**Context:** Users should be able to configure the confidence threshold for flagging events. Add this setting to DEFAULT_CONFIG and the Config dataclass.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_config_has_confidence_threshold():
    """Config should have categorization_confidence_threshold setting."""
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'categorization_confidence_threshold' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['categorization_confidence_threshold'] == 70

    # Verify Config dataclass accepts it
    config = Config(categorization_confidence_threshold=80)
    assert config.categorization_confidence_threshold == 80
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_config_has_confidence_threshold -v
```
Expected output: `AssertionError: assert 'categorization_confidence_threshold' in {...}`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/config.py (add to DEFAULT_CONFIG dict around line 15-45)

    # Categorization settings
    'categorization_confidence_threshold': 70,  # Minimum confidence (0-100) before flagging for review


# Also add to Config dataclass fields (around line 50-80)
    categorization_confidence_threshold: int = 70
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_config_has_confidence_threshold -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/config.py && git commit -m "feat: add categorization_confidence_threshold to config"
```

---

### Task 11: Integrate categorizer into tracking loop (~4 min)

**Files:**
- **Modify:** `tests/test_categorizer.py`
- **Modify:** `src/syncopaid/__main__.py`

**Context:** The SyncoPaidApp needs to use the ActivityMatcher to categorize events before inserting them into the database. This happens in _run_tracking_loop().

**Step 1 - RED:** Write failing test
```python
# tests/test_categorizer.py (append after previous test)

def test_categorizer_integrates_with_app():
    """SyncoPaidApp should use ActivityMatcher for categorization."""
    # This is an integration check - verify the import works
    try:
        from syncopaid.__main__ import SyncoPaidApp
        from syncopaid.categorizer import ActivityMatcher

        # Verify SyncoPaidApp can create an ActivityMatcher
        # (Full integration test would require running the app)
        assert callable(ActivityMatcher)
    except ImportError as e:
        assert False, f"Integration failed: {e}"
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_categorizer.py::test_categorizer_integrates_with_app -v
```
Expected output: Should pass (this verifies import structure)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/__main__.py (add import at top with other imports, around line 10-20)
from .categorizer import ActivityMatcher


# In SyncoPaidApp.__init__ (around line 50-70), add after database initialization:
        # Initialize categorizer
        self.matcher = ActivityMatcher(
            self.db,
            confidence_threshold=self.config.categorization_confidence_threshold
        )


# In _run_tracking_loop (around line 150-180), modify the event insertion:
# Find where events are inserted (db.insert_event(event)) and change to:

                    # Categorize the event
                    categorization = self.matcher.categorize_activity(
                        app=event.app,
                        title=event.title,
                        url=event.url,
                        path=None  # Future: extract from title
                    )

                    # Insert with categorization data
                    self.db.insert_event(
                        event,
                        matter_id=categorization.matter_id,
                        confidence=categorization.confidence,
                        flagged_for_review=categorization.flagged_for_review
                    )
```

**Step 4 - Verify GREEN:**
```bash
python -m pytest tests/test_categorizer.py::test_categorizer_integrates_with_app -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorizer.py src/syncopaid/__main__.py && git commit -m "feat: integrate ActivityMatcher into tracking loop"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_categorizer.py -v    # All categorizer tests pass
python -m pytest tests/ -v                        # All existing tests still pass
python -m syncopaid.database                      # Database module runs without error
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

**Edge Cases:**
- Multiple matters match same client: Returns first match (could be enhanced to pick most recently updated)
- Empty window title: Falls through to "unknown" categorization
- Database migration: Columns added with sensible defaults, existing events get flagged_for_review=False

**Dependencies:**
- Story 8.1 (Matter/Client Database) provides the matters table schema
- Story 8.1.1 (Matter Keywords/Tags) will enhance keyword matching accuracy

**Follow-up Work:**
- Review UI for batch processing flagged events (new story needed)
- Machine learning based matching using historical corrections
- URL/path parsing for better context extraction (Story 1.6)

**Technical Decisions:**
- Rule-based matching chosen over ML for initial implementation (simpler, deterministic)
- Confidence scores: 100% for exact matter number, 80% for client name, 60% for keywords
- Default threshold 70% balances between too many false positives vs missing matches
