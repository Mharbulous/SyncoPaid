"""Tests for window interaction level detection."""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
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


def test_get_interaction_level_returns_idle_when_globally_idle():
    """Verify get_interaction_level returns IDLE when idle_seconds >= threshold."""
    from syncopaid.tracker import TrackerLoop, InteractionLevel

    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        interaction_threshold=5.0
    )

    # When globally idle, should return IDLE regardless of other state
    level = tracker.get_interaction_level(idle_seconds=200.0)
    assert level == InteractionLevel.IDLE


def test_get_interaction_level_returns_passive_when_no_activity():
    """Verify get_interaction_level returns PASSIVE when no recent activity."""
    from syncopaid.tracker import TrackerLoop, InteractionLevel
    from unittest.mock import patch

    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        interaction_threshold=5.0
    )

    # Mock no keyboard/mouse activity
    with patch('syncopaid.tracker_windows.get_keyboard_activity', return_value=False):
        with patch('syncopaid.tracker_windows.get_mouse_activity', return_value=False):
            level = tracker.get_interaction_level(idle_seconds=0.0)

    # With no recent activity, should be PASSIVE
    assert level == InteractionLevel.PASSIVE


def test_finalized_event_includes_interaction_level():
    """Verify finalized ActivityEvent has interaction_level from tracking."""
    from syncopaid.tracker import TrackerLoop, InteractionLevel, ActivityEvent
    from unittest.mock import patch
    from datetime import datetime, timezone

    tracker = TrackerLoop(
        poll_interval=0.01,
        idle_threshold=180.0,
        interaction_threshold=5.0
    )

    # Simulate: window 1 with typing, then window 2 to trigger finalization
    windows = [
        {'app': 'WINWORD.EXE', 'title': 'Document.docx', 'pid': 1234},
        {'app': 'chrome.exe', 'title': 'Google', 'pid': 5678},
    ]

    call_count = [0]

    def mock_window():
        idx = min(call_count[0], len(windows) - 1)
        return windows[idx]

    def mock_idle():
        call_count[0] += 1
        return 0.0  # Not globally idle

    events = []
    with patch('syncopaid.tracker_windows.get_active_window', side_effect=mock_window):
        with patch('syncopaid.tracker_windows.get_idle_seconds', side_effect=mock_idle):
            with patch('syncopaid.tracker_windows.get_keyboard_activity', return_value=True):
                with patch('syncopaid.tracker_windows.get_mouse_activity', return_value=False):
                    with patch('time.sleep'):
                        gen = tracker.start()
                        # Get first few events
                        for _ in range(5):
                            try:
                                event = next(gen)
                                if isinstance(event, ActivityEvent):
                                    events.append(event)
                            except StopIteration:
                                break
                        tracker.stop()

    # At least one event should have typing interaction level
    assert len(events) > 0
    assert any(e.interaction_level == InteractionLevel.TYPING.value for e in events)


def test_config_has_interaction_threshold():
    """Verify config includes interaction_threshold_seconds setting."""
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'interaction_threshold_seconds' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['interaction_threshold_seconds'] == 5.0

    # Verify Config dataclass accepts it
    config = Config(interaction_threshold_seconds=10.0)
    assert config.interaction_threshold_seconds == 10.0
