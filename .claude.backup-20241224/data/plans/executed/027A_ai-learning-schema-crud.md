# 027A: AI Learning Database - Schema and CRUD Operations

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 3.6 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 027_ai-learning-database.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create the categorization_patterns table and basic CRUD operations for AI learning patterns.
**Approach:** Create table schema in database_schema.py, add PatternsDatabaseMixin with insert/get/find/delete methods.
**Tech Stack:** SQLite, Python sqlite3 module

---

## Story Context

**Title:** AI Learning Database for Categorization Patterns
**Description:** Store user corrections when they change AI categorization suggestions, building matter-specific patterns (app, URL, title) that improve categorization accuracy over time.

This sub-plan covers the foundational database work:
- [ ] Create categorization_patterns table with required schema
- [ ] Implement basic CRUD operations for patterns

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

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_categorization_patterns.py -v  # All pattern tests pass
python -m pytest tests/test_database.py -v                  # Database tests pass
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan A of 3 (027A, 027B, 027C)
- Patterns use simple wildcard matching (* and ?) converted to SQL LIKE patterns
- All pattern storage is local - no data leaves the device

## Dependencies

- Requires story 3.5 (Matter/Client Database) - `matters` table must exist
