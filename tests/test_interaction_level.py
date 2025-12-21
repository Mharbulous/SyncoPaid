"""Tests for window interaction level detection."""

import pytest
from syncopaid.tracker import InteractionLevel, ActivityEvent


def test_interaction_level_enum_values():
    """Verify InteractionLevel enum has expected values."""
    assert InteractionLevel.TYPING.value == "typing"
    assert InteractionLevel.CLICKING.value == "clicking"
    assert InteractionLevel.PASSIVE.value == "passive"
    assert InteractionLevel.IDLE.value == "idle"


def test_activity_event_has_interaction_level():
    """Verify ActivityEvent has interaction_level field with default."""
    event = ActivityEvent(
        timestamp="2025-12-19T10:00:00",
        duration_seconds=300.0,
        app="WINWORD.EXE",
        title="Contract.docx - Word"
    )

    assert hasattr(event, 'interaction_level')
    assert event.interaction_level == InteractionLevel.PASSIVE.value
