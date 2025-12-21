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


def test_is_key_pressed_returns_bool():
    """Verify is_key_pressed returns boolean."""
    from syncopaid.tracker import is_key_pressed

    # Test with a common virtual key code (0x41 = 'A')
    result = is_key_pressed(0x41)
    assert isinstance(result, bool)


def test_get_keyboard_activity_returns_bool():
    """Verify get_keyboard_activity returns boolean for any typing."""
    from syncopaid.tracker import get_keyboard_activity

    result = get_keyboard_activity()
    assert isinstance(result, bool)


def test_get_mouse_activity_returns_bool():
    """Verify get_mouse_activity returns boolean for any clicking."""
    from syncopaid.tracker import get_mouse_activity

    result = get_mouse_activity()
    assert isinstance(result, bool)


def test_tracker_loop_has_interaction_tracking_state():
    """Verify TrackerLoop has interaction tracking state variables."""
    from syncopaid.tracker import TrackerLoop

    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        interaction_threshold=5.0
    )

    assert hasattr(tracker, 'last_typing_time')
    assert tracker.last_typing_time is None
    assert hasattr(tracker, 'last_click_time')
    assert tracker.last_click_time is None
    assert hasattr(tracker, 'interaction_threshold')
    assert tracker.interaction_threshold == 5.0


def test_tracker_loop_default_interaction_threshold():
    """Verify TrackerLoop has sensible default for interaction_threshold."""
    from syncopaid.tracker import TrackerLoop

    tracker = TrackerLoop(poll_interval=1.0)

    # Default should be 5 seconds (typing/clicking within 5s = active)
    assert tracker.interaction_threshold == 5.0
