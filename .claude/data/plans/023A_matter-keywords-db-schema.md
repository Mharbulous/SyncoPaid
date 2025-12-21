# 023A: Matter Keywords/Tags - Database Schema

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-21 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add database schema and CRUD operations for AI-managed matter keywords.
**Approach:** Create `matter_keywords` table with FK to matters, add keyword CRUD methods to database mixins.
**Tech Stack:** SQLite, Python sqlite3 module

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** AI-managed keywords for matters that eliminate human error and maintain the "no manual maintenance" killer feature. AI has complete control over keyword quality and relevance.

**Acceptance Criteria:**
- [ ] Keywords stored in matters table (separate tags table)
- [ ] AI can add/update/remove keywords for matters
- [ ] Keywords displayed in matter list UI (read-only, AI-managed)

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 8.1 (Matter/Client Database) implemented - `matters` table exists
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_client.py -v`

## TDD Tasks

### Task 1: Create matter_keywords table schema (~3 min)

**Files:**
- Modify: `src/syncopaid/database_schema.py:163-199`
- Test: `tests/test_matter_keywords.py`

**Context:** The `matters` table exists (lines 181-192 in database_schema.py). We need a separate `matter_keywords` table to store AI-extracted keywords per matter, avoiding data duplication and enabling efficient queries.

**Step 1 - RED:** Write failing test
```python
# tests/test_matter_keywords.py (CREATE)
"""Test matter keywords database functionality."""
import sqlite3
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from syncopaid.database import Database


def test_matter_keywords_table_exists():
    """Verify matter_keywords table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matter_keywords'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matter_keywords table should exist"


def test_matter_keywords_table_schema():
    """Verify matter_keywords table has correct columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(matter_keywords)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'matter_id' in columns
        assert 'keyword' in columns
        assert 'source' in columns  # 'ai' or 'manual' (future)
        assert 'confidence' in columns
        assert 'created_at' in columns


if __name__ == "__main__":
    test_matter_keywords_table_exists()
    test_matter_keywords_table_schema()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_matter_keywords.py -v
```
Expected output: `FAILED` (table does not exist yet)

**Step 3 - GREEN:** Add table creation method
```python
# src/syncopaid/database_schema.py (add after line 198, after _create_clients_matters_tables)

    def _create_matter_keywords_table(self, cursor):
        """
        Create matter_keywords table for AI-managed keyword extraction.

        Keywords are extracted and managed by AI - users cannot edit directly.
        This ensures keyword quality and avoids human error in categorization.

        Args:
            cursor: Database cursor for creating table
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matter_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matter_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'ai',
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (matter_id) REFERENCES matters(id) ON DELETE CASCADE,
                UNIQUE(matter_id, keyword)
            )
        """)

        # Create index for efficient keyword lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matter_keywords_matter
            ON matter_keywords(matter_id)
        """)

        # Create index for keyword search across all matters
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matter_keywords_keyword
            ON matter_keywords(keyword)
        """)
```

Also modify `_init_schema` method (around line 59-62) to call the new method:
```python
# In _init_schema, after line 60 (_create_clients_matters_tables call):
            # Create matter keywords table for AI keyword extraction
            self._create_matter_keywords_table(cursor)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_matter_keywords.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_matter_keywords.py src/syncopaid/database_schema.py && git commit -m "feat: add matter_keywords table for AI-managed keyword extraction"
```

---

### Task 2: Add keyword CRUD operations (~5 min)

**Files:**
- Create: `src/syncopaid/database_keywords.py`
- Modify: `src/syncopaid/database.py:22-28`
- Test: `tests/test_matter_keywords.py`

**Context:** Following the mixin pattern (ConnectionMixin, SchemaMixin, OperationsMixin), we create a KeywordsDatabaseMixin for keyword CRUD operations. The Database class composes all mixins.

**Step 1 - RED:** Write failing tests
```python
# tests/test_matter_keywords.py (ADD to existing file)

def test_add_keyword_to_matter():
    """Test adding a keyword to a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client and matter first
        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        # Add keyword
        keyword_id = db.add_matter_keyword(matter_id, "contract", source="ai", confidence=0.95)
        assert keyword_id > 0


def test_get_matter_keywords():
    """Test retrieving keywords for a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        db.add_matter_keyword(matter_id, "contract", source="ai", confidence=0.95)
        db.add_matter_keyword(matter_id, "litigation", source="ai", confidence=0.87)

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 2
        assert any(k['keyword'] == 'contract' for k in keywords)
        assert any(k['keyword'] == 'litigation' for k in keywords)


def test_delete_matter_keyword():
    """Test removing a keyword from a matter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        keyword_id = db.add_matter_keyword(matter_id, "obsolete", source="ai")
        db.delete_matter_keyword(keyword_id)

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 0


def test_update_matter_keywords_batch():
    """Test replacing all keywords for a matter (AI update pattern)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        # Initial keywords
        db.add_matter_keyword(matter_id, "old_keyword", source="ai")

        # AI updates with new analysis
        new_keywords = [
            {"keyword": "contract", "confidence": 0.95},
            {"keyword": "smith_v_jones", "confidence": 0.88}
        ]
        db.update_matter_keywords(matter_id, new_keywords, source="ai")

        keywords = db.get_matter_keywords(matter_id)
        assert len(keywords) == 2
        assert not any(k['keyword'] == 'old_keyword' for k in keywords)
        assert any(k['keyword'] == 'contract' for k in keywords)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_matter_keywords.py::test_add_keyword_to_matter -v
```
Expected output: `FAILED` (method does not exist)

**Step 3 - GREEN:** Create keywords mixin
```python
# src/syncopaid/database_keywords.py (CREATE)
"""
Database operations for AI-managed matter keywords.

Keywords are extracted and updated by AI to improve activity categorization.
Users view keywords read-only; AI has full control over keyword maintenance.
"""

import logging
from typing import List, Dict, Optional


class KeywordsDatabaseMixin:
    """
    Mixin providing matter keyword operations.

    Requires _get_connection() method from ConnectionMixin.
    """

    def add_matter_keyword(
        self,
        matter_id: int,
        keyword: str,
        source: str = "ai",
        confidence: float = 1.0
    ) -> int:
        """
        Add a keyword to a matter.

        Args:
            matter_id: ID of the matter
            keyword: The keyword text (lowercase, normalized)
            source: Origin of keyword ('ai' for AI-extracted)
            confidence: AI confidence score (0.0-1.0)

        Returns:
            ID of the inserted keyword record
        """
        keyword = keyword.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO matter_keywords
                (matter_id, keyword, source, confidence)
                VALUES (?, ?, ?, ?)
            """, (matter_id, keyword, source, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_matter_keywords(self, matter_id: int) -> List[Dict]:
        """
        Get all keywords for a matter.

        Args:
            matter_id: ID of the matter

        Returns:
            List of keyword dicts with id, keyword, source, confidence, created_at
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, keyword, source, confidence, created_at
                FROM matter_keywords
                WHERE matter_id = ?
                ORDER BY confidence DESC, keyword ASC
            """, (matter_id,))
            return cursor.fetchall()

    def delete_matter_keyword(self, keyword_id: int) -> bool:
        """
        Delete a keyword by ID.

        Args:
            keyword_id: ID of the keyword record

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM matter_keywords WHERE id = ?", (keyword_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_matter_keywords(
        self,
        matter_id: int,
        keywords: List[Dict],
        source: str = "ai"
    ) -> int:
        """
        Replace all keywords for a matter with new AI-extracted keywords.

        This is the primary method for AI keyword updates - removes old keywords
        and inserts the new set atomically.

        Args:
            matter_id: ID of the matter
            keywords: List of dicts with 'keyword' and optional 'confidence'
            source: Origin of keywords ('ai' for AI-extracted)

        Returns:
            Number of keywords inserted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Remove existing keywords from this source
            cursor.execute(
                "DELETE FROM matter_keywords WHERE matter_id = ? AND source = ?",
                (matter_id, source)
            )

            # Insert new keywords
            count = 0
            for kw in keywords:
                keyword = kw.get('keyword', '').lower().strip()
                if not keyword:
                    continue
                confidence = float(kw.get('confidence', 1.0))
                cursor.execute("""
                    INSERT OR REPLACE INTO matter_keywords
                    (matter_id, keyword, source, confidence)
                    VALUES (?, ?, ?, ?)
                """, (matter_id, keyword, source, confidence))
                count += 1

            conn.commit()
            logging.info(f"Updated {count} keywords for matter {matter_id}")
            return count

    def find_matters_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Find all matters that have a specific keyword.

        Args:
            keyword: Keyword to search for (case-insensitive)

        Returns:
            List of matter dicts with id, matter_number, description
        """
        keyword = keyword.lower().strip()
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT m.id, m.matter_number, m.description, mk.confidence
                FROM matters m
                INNER JOIN matter_keywords mk ON m.id = mk.matter_id
                WHERE mk.keyword = ?
                ORDER BY mk.confidence DESC
            """, (keyword,))
            return cursor.fetchall()

    @staticmethod
    def _dict_factory(cursor, row):
        """Convert SQLite row to dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
```

Update Database class to include the mixin:
```python
# src/syncopaid/database.py (modify lines 15-28)

from .database_connection import ConnectionMixin
from .database_schema import SchemaMixin
from .database_operations import OperationsMixin
from .database_screenshots import ScreenshotDatabaseMixin
from .database_statistics import StatisticsDatabaseMixin, format_duration
from .database_keywords import KeywordsDatabaseMixin


class Database(
    ConnectionMixin,
    SchemaMixin,
    OperationsMixin,
    ScreenshotDatabaseMixin,
    StatisticsDatabaseMixin,
    KeywordsDatabaseMixin
):
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_matter_keywords.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_keywords.py src/syncopaid/database.py tests/test_matter_keywords.py && git commit -m "feat: add keyword CRUD operations for AI-managed matter keywords"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_matter_keywords.py -v  # All keyword tests pass
python -m pytest tests/test_matter_client.py -v    # Existing tests still pass
python -m syncopaid.database                        # Module runs without error
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Keywords are stored lowercase and trimmed for consistent matching
- The `source` column supports 'ai' (default) - future enhancement could add 'manual' for user-added keywords
- `confidence` score allows AI to express certainty about keyword relevance
- CASCADE delete ensures keywords are removed when matter is deleted
- The `find_matters_by_keyword()` method supports future AI matching - given activity keywords, find matching matters

## Dependencies

None - this is the first sub-plan for story 8.1.1.

## Next Task

After this: `023B_matter-keywords-ai-extraction.md`
