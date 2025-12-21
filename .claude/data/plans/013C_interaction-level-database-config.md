# Window Interaction Level Detection - Part C: Database & Config

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add database schema migration for interaction_level and config setting for interaction threshold.
**Approach:** Extend database schema with new column and add configurable threshold setting.
**Tech Stack:** SQLite, existing database.py and config.py infrastructure

---

**Story ID:** 1.1.3 | **Created:** 2025-12-19 | **Stage:** `planned`
**Sub-plan:** C of 3 (Database & Config)
**Depends on:** 013B_interaction-level-method-integration.md

---

## Story Context

**Title:** Window Interaction Level Detection
**Description:** Current idle detection (tracker.py:174-197) uses GetLastInputInfo to detect global user activity, but doesn't distinguish between active typing in Word vs passive reading of a PDF. Lawyers need granular time attribution: 15 minutes reading a contract should be billable but categorized differently than 15 minutes drafting a motion.

**Acceptance Criteria (this sub-plan):**
- [ ] Store interaction level in database events table
- [ ] Add database migration for interaction_level column
- [ ] Add interaction_threshold_seconds config setting

## Prerequisites

- [ ] Sub-plan A completed (InteractionLevel enum, detection functions, tracker state)
- [ ] Sub-plan B completed (get_interaction_level method, loop integration)
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 6: Add Database Schema Migration for interaction_level (~4 min)

**Files:**
- **Modify:** `src/syncopaid/database.py:67-142` (_init_schema method)
- **Modify:** `src/syncopaid/database.py:144-175` (insert_event method)
- **Modify:** `src/syncopaid/database.py:252-271` (get_events method)
- **Create:** `tests/test_interaction_level_db.py`

**Context:** The database needs to store interaction_level. We add a schema migration similar to the existing state column migration.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level_db.py
"""Tests for interaction level database storage."""

import pytest
import tempfile
import os
from syncopaid.database import Database
from syncopaid.tracker import ActivityEvent, InteractionLevel


def test_database_stores_interaction_level():
    """Verify database stores and retrieves interaction_level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=300.0,
            app="WINWORD.EXE",
            title="Document.docx",
            interaction_level=InteractionLevel.TYPING.value
        )

        event_id = db.insert_event(event)
        assert event_id > 0

        events = db.get_events()
        assert len(events) == 1
        assert events[0]['interaction_level'] == "typing"


def test_database_migration_adds_interaction_level_column():
    """Verify schema migration adds interaction_level column."""
    import sqlite3

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")

        # Create database (runs migration)
        db = Database(db_path)

        # Check column exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert 'interaction_level' in columns
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level_db.py -v
```
Expected output: `FAILED` (interaction_level column doesn't exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (modify _init_schema, add after state column migration, around line 112)
            # Migration: Add interaction_level column if it doesn't exist
            if 'interaction_level' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN interaction_level TEXT DEFAULT 'passive'")
                logging.info("Database migration: Added interaction_level column to events table")
```

```python
# src/syncopaid/database.py (modify insert_event method, around line 154-175)
    def insert_event(self, event: ActivityEvent) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')
            interaction_level = getattr(event, 'interaction_level', 'passive')

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, interaction_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                1 if event.is_idle else 0,
                state,
                interaction_level
            ))

            return cursor.lastrowid
```

```python
# src/syncopaid/database.py (modify get_events method, around line 252-271)
# Update the event dictionary creation to include interaction_level:
                # Get interaction_level with fallback for older records
                if 'interaction_level' in row.keys() and row['interaction_level']:
                    interaction_level = row['interaction_level']
                else:
                    interaction_level = 'passive'

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
                    'interaction_level': interaction_level
                })
```

```python
# src/syncopaid/database.py (modify insert_events_batch method, around line 193-202)
            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, interaction_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url, 1 if e.is_idle else 0,
                 getattr(e, 'state', 'Active'),
                 getattr(e, 'interaction_level', 'passive'))
                for e in events
            ])
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level_db.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level_db.py src/syncopaid/database.py && git commit -m "feat: add interaction_level column to database schema"
```

---

### Task 7: Add Config Setting for interaction_threshold (~3 min)

**Files:**
- **Modify:** `src/syncopaid/config.py:16-39` (DEFAULT_CONFIG)
- **Modify:** `src/syncopaid/config.py:42-90` (Config dataclass)
- **Modify:** `tests/test_interaction_level.py` (add config test)

**Context:** The interaction_threshold should be configurable so users can tune sensitivity. Following the existing config patterns.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

def test_config_has_interaction_threshold():
    """Verify config includes interaction_threshold_seconds setting."""
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'interaction_threshold_seconds' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['interaction_threshold_seconds'] == 5.0

    # Verify Config dataclass accepts it
    config = Config(interaction_threshold_seconds=10.0)
    assert config.interaction_threshold_seconds == 10.0
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_config_has_interaction_threshold -v
```
Expected output: `FAILED` (interaction_threshold_seconds not in config)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/config.py (add to DEFAULT_CONFIG dict, around line 38)
    # Interaction level detection
    "interaction_threshold_seconds": 5.0
```

```python
# src/syncopaid/config.py (add to Config dataclass, around line 89)
    # Interaction level detection
    interaction_threshold_seconds: float = 5.0
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_config_has_interaction_threshold -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/config.py && git commit -m "feat: add interaction_threshold_seconds to config"
```

---

## Final Verification (Sub-plan C - Complete Feature)

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid.tracker            # Module runs without error (30s test)
python -m syncopaid.database           # Database module runs
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- **Backward compatibility**: Database migration defaults existing records to 'passive'
- **Follow-up work**: Story 8.5 (LLM API Integration) can use interaction_level for better categorization hints
- **Privacy maintained**: Only tracks timing of activity, never keystroke content
