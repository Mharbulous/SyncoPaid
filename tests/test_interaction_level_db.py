"""Tests for interaction level database storage."""

import pytest
import tempfile
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
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
