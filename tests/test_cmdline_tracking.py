"""Tests for process command line tracking functionality."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from syncopaid.tracker import ActivityEvent


def test_activity_event_has_cmdline_field():
    """Verify ActivityEvent includes optional cmdline field."""
    event = ActivityEvent(
        timestamp="2025-12-19T10:00:00+00:00",
        duration_seconds=60.0,
        app="chrome.exe",
        title="Google - Google Chrome",
        cmdline=["chrome.exe", "--profile-directory=Default"]
    )
    assert hasattr(event, 'cmdline')
    assert event.cmdline == ["chrome.exe", "--profile-directory=Default"]


def test_activity_event_cmdline_defaults_to_none():
    """Verify cmdline defaults to None for backward compatibility."""
    event = ActivityEvent(
        timestamp="2025-12-19T10:00:00+00:00",
        duration_seconds=60.0,
        app="chrome.exe",
        title="Test"
    )
    assert event.cmdline is None


def test_activity_event_to_dict_includes_cmdline():
    """Verify to_dict() includes cmdline field."""
    event = ActivityEvent(
        timestamp="2025-12-19T10:00:00+00:00",
        duration_seconds=60.0,
        app="chrome.exe",
        title="Test",
        cmdline=["chrome.exe", "--profile-directory=Work"]
    )
    data = event.to_dict()
    assert 'cmdline' in data
    assert data['cmdline'] == ["chrome.exe", "--profile-directory=Work"]


if __name__ == "__main__":
    test_activity_event_has_cmdline_field()
    test_activity_event_cmdline_defaults_to_none()
    test_activity_event_to_dict_includes_cmdline()
    print("All tests passed!")
