"""Tests for activity-to-matter categorization."""
import pytest
import tempfile
from pathlib import Path
from syncopaid.database import Database
from syncopaid.categorizer import ActivityMatcher, CategorizationResult


def test_activity_matcher_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matcher = ActivityMatcher(db)
        assert matcher.db is db
        assert matcher.confidence_threshold == 70


def test_categorize_activity_returns_unknown_when_no_matters():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matcher = ActivityMatcher(db)

        result = matcher.categorize_activity(
            app="WINWORD.EXE", title="Document.docx"
        )

        assert result.matter_id is None
        assert result.confidence == 0
        assert result.flagged_for_review is True


def test_exact_matter_number_match_in_title():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matter_id = db.insert_matter(
            matter_number="2024-001",
            description="Smith Contract Review"
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="2024-001 Smith Agreement v3.docx - Microsoft Word"
        )

        assert result.matter_id == matter_id
        assert result.matter_number == "2024-001"
        assert result.confidence == 100
        assert result.flagged_for_review is False


def test_client_name_match_in_title():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        client_id = db.insert_client(name="Acme Corporation")
        matter_id = db.insert_matter(
            matter_number="2024-002", client_id=client_id
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="chrome.exe",
            title="Acme Corporation - Patent Search - Chrome"
        )

        assert result.matter_id == matter_id
        assert result.confidence == 80


def test_description_keyword_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        matter_id = db.insert_matter(
            matter_number="2024-003",
            description="Employment Agreement Negotiation"
        )

        matcher = ActivityMatcher(db)
        result = matcher.categorize_activity(
            app="WINWORD.EXE",
            title="Employment Contract Template.docx"
        )

        assert result.matter_id == matter_id
        assert result.confidence == 60
        assert result.flagged_for_review is True  # 60 < 70 threshold


def test_events_table_has_categorization_columns():
    import sqlite3
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))

        conn = sqlite3.connect(Path(tmpdir) / "test.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'matter_id' in columns
        assert 'confidence' in columns
        assert 'flagged_for_review' in columns


def test_insert_event_with_categorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        matter_id = db.insert_matter(matter_number="TEST", description="Test")
        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=60.0,
            app="test.exe", title="Test"
        )

        db.insert_event(event, matter_id=matter_id, confidence=85)
        events = db.get_events()

        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 85


def test_get_flagged_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        # High confidence - not flagged
        db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:00:00", duration_seconds=60, app="test", title="High"),
            confidence=90, flagged_for_review=False
        )
        # Low confidence - flagged
        db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:01:00", duration_seconds=60, app="test", title="Low"),
            confidence=50, flagged_for_review=True
        )

        flagged = db.get_flagged_events()
        assert len(flagged) == 1
        assert flagged[0]['title'] == "Low"


def test_update_event_categorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        matter_id = db.insert_matter(matter_number="REVIEW", description="Test")
        event_id = db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:00:00", duration_seconds=60, app="test", title="Needs review"),
            confidence=50, flagged_for_review=True
        )

        db.update_event_categorization(event_id, matter_id=matter_id, confidence=100)

        events = db.get_events()
        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 100
        assert events[0]['flagged_for_review'] is False
