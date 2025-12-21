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
