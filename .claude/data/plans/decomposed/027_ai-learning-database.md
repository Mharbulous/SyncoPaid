# 027: AI Learning Database for Categorization Patterns

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 3.6 | **Created:** 2025-12-21 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a learning database that stores user corrections and builds matter-specific patterns for AI categorization improvement.
**Approach:** Create `categorization_patterns` table, implement pattern storage/retrieval methods, add confidence scoring and expiration logic.
**Tech Stack:** SQLite, Python sqlite3 module

---

## Story Context

**Title:** AI Learning Database for Categorization Patterns
**Description:** Store user corrections when they change AI categorization suggestions, building matter-specific patterns (app, URL, title) that improve categorization accuracy over time.

**Acceptance Criteria:**
- [ ] Create categorization_patterns table with: pattern_id, matter_id, app_pattern, url_pattern, title_pattern, confidence_score, created_at, last_used_at
- [ ] Store user corrections: when user changes activity from AI suggestion to different matter, record the pattern
- [ ] Query patterns during categorization: match activity against stored patterns for matter suggestions
- [ ] Confidence scoring: increase confidence when pattern matches repeatedly, decrease when corrections contradict it
- [ ] Pattern expiration: archive patterns not used in 90 days to prevent stale suggestions
- [ ] Export patterns in JSON export for external AI/LLM context
- [ ] Privacy: patterns stored locally only, never leave device

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 3.5 (Matter/Client Database) implemented - `matters` table exists
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_client.py -v`

## TDD Tasks

### Task 1: Create categorization_patterns table schema (~3 min)

**Files:**
- Modify: `src/syncopaid/database_schema.py:163-199`
- Test: `tests/test_categorization_patterns.py`

**Context:** The `matters` table exists (lines 181-192 in database_schema.py). We need a `categorization_patterns` table to store learned patterns that map activity attributes to matters. Patterns include app names, URL patterns, and title patterns.

**Step 1 - RED:** Write failing test
```python
# tests/test_categorization_patterns.py (CREATE)
"""Test AI learning database for categorization patterns."""
import sqlite3
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


def test_categorization_patterns_table_exists():
    """Verify categorization_patterns table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categorization_patterns'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "categorization_patterns table should exist"


def test_categorization_patterns_table_schema():
    """Verify categorization_patterns table has correct columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(categorization_patterns)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Required columns from acceptance criteria
        assert 'id' in columns
        assert 'matter_id' in columns
        assert 'app_pattern' in columns
        assert 'url_pattern' in columns
        assert 'title_pattern' in columns
        assert 'confidence_score' in columns
        assert 'created_at' in columns
        assert 'last_used_at' in columns


if __name__ == "__main__":
    test_categorization_patterns_table_exists()
    test_categorization_patterns_table_schema()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: `FAILED` (table does not exist yet)

**Step 3 - GREEN:** Add table creation method
```python
# src/syncopaid/database_schema.py (add after _create_clients_matters_tables method)

    def _create_categorization_patterns_table(self, cursor):
        """
        Create categorization_patterns table for AI learning.

        Stores user corrections to build matter-specific patterns that
        improve categorization accuracy over time. Patterns match on
        app name, URL, and/or window title.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorization_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matter_id INTEGER NOT NULL,
                app_pattern TEXT,
                url_pattern TEXT,
                title_pattern TEXT,
                confidence_score REAL NOT NULL DEFAULT 1.0,
                match_count INTEGER NOT NULL DEFAULT 1,
                correction_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_used_at TEXT NOT NULL DEFAULT (datetime('now')),
                is_archived INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (matter_id) REFERENCES matters(id) ON DELETE CASCADE
            )
        """)

        # Index for efficient pattern lookups during categorization
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_app
            ON categorization_patterns(app_pattern)
            WHERE app_pattern IS NOT NULL AND is_archived = 0
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_matter
            ON categorization_patterns(matter_id)
            WHERE is_archived = 0
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_last_used
            ON categorization_patterns(last_used_at)
            WHERE is_archived = 0
        """)
```

Also modify `_init_schema` method (around line 59-62) to call the new method:
```python
# In _init_schema, after _create_clients_matters_tables call:
            # Create categorization patterns table for AI learning
            self._create_categorization_patterns_table(cursor)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_categorization_patterns.py src/syncopaid/database_schema.py && git commit -m "feat: add categorization_patterns table for AI learning"
```

---

### Task 2: Add pattern CRUD operations (~5 min)

**Files:**
- Create: `src/syncopaid/database_patterns.py`
- Modify: `src/syncopaid/database.py:15-28`
- Test: `tests/test_categorization_patterns.py`

**Context:** Following the mixin pattern used by other database modules (ConnectionMixin, SchemaMixin, OperationsMixin), create a PatternsDatabaseMixin for pattern CRUD operations.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)

def test_insert_pattern():
    """Test inserting a new categorization pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first
        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        # Insert pattern
        pattern_id = db.insert_pattern(
            matter_id=matter_id,
            app_pattern="WINWORD.EXE",
            title_pattern="Contract*"
        )
        assert pattern_id > 0


def test_get_patterns_for_matter():
    """Test retrieving patterns for a specific matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE")
        db.insert_pattern(matter_id, url_pattern="*canlii.org*")

        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 2


def test_find_matching_patterns():
    """Test finding patterns that match activity attributes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE", confidence_score=0.9)

        # Should match
        matches = db.find_matching_patterns(app="WINWORD.EXE")
        assert len(matches) == 1
        assert matches[0]['matter_id'] == matter_id

        # Should not match
        no_matches = db.find_matching_patterns(app="chrome.exe")
        assert len(no_matches) == 0


def test_delete_pattern():
    """Test deleting a pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        pattern_id = db.insert_pattern(matter_id, app_pattern="test.exe")
        db.delete_pattern(pattern_id)

        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 0
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_insert_pattern -v
```
Expected output: `FAILED` (method does not exist)

**Step 3 - GREEN:** Create patterns mixin
```python
# src/syncopaid/database_patterns.py (CREATE)
"""
Database operations for AI categorization learning patterns.

Patterns are created from user corrections when they change AI categorization
suggestions. Each pattern maps activity attributes (app, URL, title) to a matter.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime


class PatternsDatabaseMixin:
    """
    Mixin providing categorization pattern operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def insert_pattern(
        self,
        matter_id: int,
        app_pattern: Optional[str] = None,
        url_pattern: Optional[str] = None,
        title_pattern: Optional[str] = None,
        confidence_score: float = 1.0
    ) -> int:
        """
        Insert a new categorization pattern.

        Args:
            matter_id: ID of the matter this pattern maps to
            app_pattern: Application name pattern (exact or wildcard)
            url_pattern: URL pattern (supports wildcards)
            title_pattern: Window title pattern (supports wildcards)
            confidence_score: Initial confidence (0.0-1.0)

        Returns:
            ID of the inserted pattern
        """
        if not any([app_pattern, url_pattern, title_pattern]):
            raise ValueError("At least one pattern (app, url, or title) is required")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categorization_patterns
                (matter_id, app_pattern, url_pattern, title_pattern, confidence_score)
                VALUES (?, ?, ?, ?, ?)
            """, (matter_id, app_pattern, url_pattern, title_pattern, confidence_score))
            conn.commit()
            logging.debug(f"Inserted pattern {cursor.lastrowid} for matter {matter_id}")
            return cursor.lastrowid

    def get_patterns_for_matter(self, matter_id: int, include_archived: bool = False) -> List[Dict]:
        """
        Get all patterns for a specific matter.

        Args:
            matter_id: ID of the matter
            include_archived: Whether to include archived patterns

        Returns:
            List of pattern dictionaries
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            if include_archived:
                cursor.execute("""
                    SELECT * FROM categorization_patterns
                    WHERE matter_id = ?
                    ORDER BY confidence_score DESC, last_used_at DESC
                """, (matter_id,))
            else:
                cursor.execute("""
                    SELECT * FROM categorization_patterns
                    WHERE matter_id = ? AND is_archived = 0
                    ORDER BY confidence_score DESC, last_used_at DESC
                """, (matter_id,))

            return cursor.fetchall()

    def find_matching_patterns(
        self,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> List[Dict]:
        """
        Find patterns matching the given activity attributes.

        Uses exact matching for app_pattern and LIKE matching for url/title.
        Returns patterns sorted by confidence score descending.

        Args:
            app: Application name to match
            url: URL to match
            title: Window title to match

        Returns:
            List of matching pattern dicts with matter_id and confidence_score
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            conditions = ["is_archived = 0"]
            params = []

            # Build OR conditions for pattern matching
            pattern_conditions = []

            if app:
                pattern_conditions.append("(app_pattern IS NOT NULL AND app_pattern = ?)")
                params.append(app)

            if url:
                pattern_conditions.append("(url_pattern IS NOT NULL AND ? LIKE REPLACE(REPLACE(url_pattern, '*', '%'), '?', '_'))")
                params.append(url)

            if title:
                pattern_conditions.append("(title_pattern IS NOT NULL AND ? LIKE REPLACE(REPLACE(title_pattern, '*', '%'), '?', '_'))")
                params.append(title)

            if not pattern_conditions:
                return []

            conditions.append(f"({' OR '.join(pattern_conditions)})")

            query = f"""
                SELECT cp.*, m.matter_number, m.description as matter_description
                FROM categorization_patterns cp
                JOIN matters m ON cp.matter_id = m.id
                WHERE {' AND '.join(conditions)}
                ORDER BY cp.confidence_score DESC, cp.match_count DESC
            """

            cursor.execute(query, params)
            return cursor.fetchall()

    def delete_pattern(self, pattern_id: int) -> bool:
        """
        Delete a pattern by ID.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorization_patterns WHERE id = ?", (pattern_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def _dict_factory(cursor, row):
        """Convert SQLite row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
```

Update Database class to include the mixin:
```python
# src/syncopaid/database.py (modify imports and class definition)

from .database_connection import ConnectionMixin
from .database_schema import SchemaMixin
from .database_operations import OperationsMixin
from .database_screenshots import ScreenshotDatabaseMixin
from .database_statistics import StatisticsDatabaseMixin
from .database_patterns import PatternsDatabaseMixin


class Database(
    ConnectionMixin,
    SchemaMixin,
    OperationsMixin,
    ScreenshotDatabaseMixin,
    StatisticsDatabaseMixin,
    PatternsDatabaseMixin
):
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py src/syncopaid/database.py tests/test_categorization_patterns.py && git commit -m "feat: add pattern CRUD operations for AI learning"
```

---

### Task 3: Implement user correction recording (~4 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** When a user corrects an AI categorization (changes activity from one matter to another), we record the activity's attributes as a new pattern for the corrected matter.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)

def test_record_user_correction():
    """Test recording a user correction creates appropriate pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        # User corrects: activity was misclassified, should be matter 2024-001
        pattern_id = db.record_correction(
            matter_id=matter_id,
            app="WINWORD.EXE",
            url=None,
            title="Smith Contract Draft.docx - Word"
        )

        assert pattern_id > 0

        # Pattern should now match similar activities
        matches = db.find_matching_patterns(app="WINWORD.EXE")
        assert len(matches) == 1
        assert matches[0]['matter_id'] == matter_id


def test_duplicate_correction_increases_confidence():
    """Test that repeated corrections increase pattern confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        # First correction
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)
        initial_confidence = patterns[0]['confidence_score']
        initial_count = patterns[0]['match_count']

        # Same correction again - should reinforce pattern
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)

        assert patterns[0]['match_count'] > initial_count
        assert patterns[0]['confidence_score'] >= initial_confidence
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_record_user_correction -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add correction recording method
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

    def record_correction(
        self,
        matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction to create or reinforce a pattern.

        When user corrects AI categorization, record the activity's attributes
        as a pattern for the correct matter. If pattern already exists,
        increase confidence and match count.

        Args:
            matter_id: Correct matter ID (what user selected)
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or updated pattern
        """
        if not any([app, url, title]):
            raise ValueError("At least one attribute (app, url, or title) is required")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Check if pattern already exists
            cursor.execute("""
                SELECT id, match_count, confidence_score
                FROM categorization_patterns
                WHERE matter_id = ?
                AND (app_pattern = ? OR (app_pattern IS NULL AND ? IS NULL))
                AND (url_pattern = ? OR (url_pattern IS NULL AND ? IS NULL))
                AND (title_pattern = ? OR (title_pattern IS NULL AND ? IS NULL))
                AND is_archived = 0
            """, (matter_id, app, app, url, url, title, title))

            existing = cursor.fetchone()

            if existing:
                # Reinforce existing pattern
                pattern_id, match_count, confidence = existing
                new_count = match_count + 1
                # Increase confidence slightly, max 1.0
                new_confidence = min(1.0, confidence + 0.05)

                cursor.execute("""
                    UPDATE categorization_patterns
                    SET match_count = ?, confidence_score = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_count, new_confidence, now, pattern_id))
                conn.commit()
                logging.info(f"Reinforced pattern {pattern_id}: count={new_count}, confidence={new_confidence:.2f}")
                return pattern_id
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO categorization_patterns
                    (matter_id, app_pattern, url_pattern, title_pattern, confidence_score, last_used_at)
                    VALUES (?, ?, ?, ?, 1.0, ?)
                """, (matter_id, app, url, title, now))
                conn.commit()
                pattern_id = cursor.lastrowid
                logging.info(f"Created new pattern {pattern_id} for matter {matter_id}")
                return pattern_id
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add user correction recording for AI learning"
```

---

### Task 4: Implement confidence adjustment on contradictions (~4 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** When a user corrects an activity to a *different* matter than an existing pattern suggests, we should decrease confidence of the old pattern.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)

def test_contradicting_correction_decreases_confidence():
    """Test that contradicting corrections decrease old pattern confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_a = db.insert_matter("2024-001", client_id, "Matter A")
        matter_b = db.insert_matter("2024-002", client_id, "Matter B")

        # Initial pattern: WINWORD.EXE -> Matter A
        db.insert_pattern(matter_a, app_pattern="WINWORD.EXE", confidence_score=0.9)

        # User correction: same app but different matter
        db.record_correction_with_contradiction(
            correct_matter_id=matter_b,
            app="WINWORD.EXE"
        )

        # Old pattern confidence should decrease
        patterns_a = db.get_patterns_for_matter(matter_a)
        assert patterns_a[0]['confidence_score'] < 0.9
        assert patterns_a[0]['correction_count'] > 0

        # New pattern for matter B should exist
        patterns_b = db.get_patterns_for_matter(matter_b)
        assert len(patterns_b) == 1
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_contradicting_correction_decreases_confidence -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add contradiction handling
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

    def record_correction_with_contradiction(
        self,
        correct_matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction that may contradict existing patterns.

        This is the primary method for handling user corrections. It:
        1. Finds any existing patterns that match these attributes
        2. Decreases confidence of patterns pointing to OTHER matters
        3. Creates/reinforces pattern for the correct matter

        Args:
            correct_matter_id: The matter user selected as correct
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or reinforced pattern
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Find existing patterns that match these attributes but point elsewhere
            contradicting_patterns = []
            if app:
                cursor.execute("""
                    SELECT id, confidence_score, correction_count
                    FROM categorization_patterns
                    WHERE app_pattern = ? AND matter_id != ? AND is_archived = 0
                """, (app, correct_matter_id))
                contradicting_patterns.extend(cursor.fetchall())

            # Decrease confidence of contradicting patterns
            for pattern_id, confidence, corrections in contradicting_patterns:
                new_confidence = max(0.1, confidence - 0.1)  # Min 0.1
                new_corrections = corrections + 1
                cursor.execute("""
                    UPDATE categorization_patterns
                    SET confidence_score = ?, correction_count = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_confidence, new_corrections, now, pattern_id))
                logging.info(f"Decreased confidence of pattern {pattern_id} to {new_confidence:.2f}")

            conn.commit()

        # Now record the correct pattern (will create or reinforce)
        return self.record_correction(correct_matter_id, app, url, title)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add confidence adjustment for contradicting corrections"
```

---

### Task 5: Implement pattern expiration (90-day archive) (~3 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** Patterns not used in 90 days should be archived to prevent stale suggestions from affecting categorization.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)
from datetime import datetime, timedelta

def test_archive_stale_patterns():
    """Test archiving patterns not used in 90 days."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        # Insert pattern with old last_used_at
        db.insert_pattern(matter_id, app_pattern="old_app.exe")

        # Manually set last_used_at to 100 days ago
        conn = sqlite3.connect(db_path)
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        conn.execute("UPDATE categorization_patterns SET last_used_at = ?", (old_date,))
        conn.commit()
        conn.close()

        # Run expiration
        archived_count = db.archive_stale_patterns(days=90)

        assert archived_count == 1

        # Pattern should not appear in normal queries
        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 0

        # But should appear if including archived
        patterns = db.get_patterns_for_matter(matter_id, include_archived=True)
        assert len(patterns) == 1
        assert patterns[0]['is_archived'] == 1
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_archive_stale_patterns -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add expiration method
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

    def archive_stale_patterns(self, days: int = 90) -> int:
        """
        Archive patterns that haven't been used in the specified number of days.

        Archived patterns are excluded from matching but retained for analysis.

        Args:
            days: Number of days of inactivity before archiving (default: 90)

        Returns:
            Number of patterns archived
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                UPDATE categorization_patterns
                SET is_archived = 1
                WHERE is_archived = 0
                AND last_used_at < ?
            """, (cutoff_date,))

            archived = cursor.rowcount
            conn.commit()

            if archived > 0:
                logging.info(f"Archived {archived} stale patterns (unused for {days}+ days)")

            return archived
```

Also add the timedelta import at the top of the file:
```python
from datetime import datetime, timedelta
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add pattern expiration for stale pattern archival"
```

---

### Task 6: Add patterns to JSON export (~4 min)

**Files:**
- Modify: `src/syncopaid/exporter.py:43-113`
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** Patterns should be exportable in JSON for external AI/LLM context. The Exporter class handles JSON exports (lines 43-113). We add a method to export patterns and integrate it into the main export.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)
import json

def test_export_patterns_for_llm():
    """Test exporting patterns in LLM-friendly JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE", confidence_score=0.95)
        db.insert_pattern(matter_id, url_pattern="*canlii.org*", confidence_score=0.8)

        # Export patterns
        patterns_json = db.export_patterns_json()
        patterns = json.loads(patterns_json)

        assert 'patterns' in patterns
        assert len(patterns['patterns']) == 2
        assert any(p['app_pattern'] == 'WINWORD.EXE' for p in patterns['patterns'])


def test_get_all_active_patterns():
    """Test retrieving all active patterns for export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_a = db.insert_matter("2024-001", client_id, "Matter A")
        matter_b = db.insert_matter("2024-002", client_id, "Matter B")

        db.insert_pattern(matter_a, app_pattern="app1.exe")
        db.insert_pattern(matter_b, app_pattern="app2.exe")

        all_patterns = db.get_all_patterns()
        assert len(all_patterns) == 2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_export_patterns_for_llm -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add export methods
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)
import json

    def get_all_patterns(self, include_archived: bool = False) -> List[Dict]:
        """
        Get all patterns across all matters.

        Args:
            include_archived: Whether to include archived patterns

        Returns:
            List of all pattern dictionaries with matter info
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            archive_filter = "" if include_archived else "WHERE cp.is_archived = 0"

            cursor.execute(f"""
                SELECT cp.*, m.matter_number, m.description as matter_description,
                       c.name as client_name
                FROM categorization_patterns cp
                JOIN matters m ON cp.matter_id = m.id
                LEFT JOIN clients c ON m.client_id = c.id
                {archive_filter}
                ORDER BY cp.confidence_score DESC, cp.match_count DESC
            """)
            return cursor.fetchall()

    def export_patterns_json(self, include_archived: bool = False) -> str:
        """
        Export all patterns in JSON format for LLM context.

        Format is optimized for including in AI prompts for categorization.
        Privacy: This export is local-only, for user's external AI tools.

        Args:
            include_archived: Whether to include archived patterns

        Returns:
            JSON string with patterns data
        """
        patterns = self.get_all_patterns(include_archived)

        # Format for LLM consumption
        export_data = {
            "export_date": datetime.now().isoformat(),
            "pattern_count": len(patterns),
            "patterns": [
                {
                    "matter_number": p['matter_number'],
                    "matter_description": p['matter_description'],
                    "client_name": p.get('client_name'),
                    "app_pattern": p['app_pattern'],
                    "url_pattern": p['url_pattern'],
                    "title_pattern": p['title_pattern'],
                    "confidence": p['confidence_score'],
                    "match_count": p['match_count']
                }
                for p in patterns
            ]
        }

        return json.dumps(export_data, indent=2)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add pattern export for LLM context"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_categorization_patterns.py -v  # All pattern tests pass
python -m pytest tests/test_matter_client.py -v             # Existing tests still pass
python -m pytest tests/test_database.py -v                   # Database tests pass
python -m syncopaid.database                                  # Module runs without error
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Patterns use simple wildcard matching (* and ?) converted to SQL LIKE patterns
- Confidence scores range from 0.1 (very low) to 1.0 (certain)
- Archived patterns are soft-deleted and can be restored if needed
- The `export_patterns_json()` method produces local-only output for user's external AI tools
- All pattern storage is local - no data leaves the device

## Dependencies

- Requires story 3.5 (Matter/Client Database) - `matters` table must exist

## Future Enhancements

After this story:
- Story 15.1 (Automatic Screenshot Analysis) can use patterns for initial categorization hints
- Story 15.5 (Review and Correction Interface) will call `record_correction_with_contradiction()` on user actions
