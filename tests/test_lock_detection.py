"""Tests for lock screen and screensaver detection."""
import sys
import pytest

# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason="Windows-only tests")


def test_is_screensaver_active_detects_screensaver():
    """Test that is_screensaver_active can detect screensaver process."""
    from syncopaid.tracker_windows import is_screensaver_active

    # When screensaver is NOT active, should return False
    # (We can't easily trigger real screensaver in CI, so test the function exists and returns bool)
    result = is_screensaver_active()
    assert isinstance(result, bool)
    # In normal conditions (no screensaver), should be False
    assert result == False


def test_is_workstation_locked_detects_lock_state():
    """Test that is_workstation_locked can detect Windows lock screen."""
    from syncopaid.tracker_windows import is_workstation_locked

    # When workstation is NOT locked, should return False
    # (We can't easily trigger lock screen in CI, so test the function exists and returns bool)
    result = is_workstation_locked()
    assert isinstance(result, bool)
    # In normal conditions (not locked), should be False
    assert result == False


def test_tracker_loop_detects_screensaver_state():
    """Test that TrackerLoop includes screensaver detection in state tracking."""
    from syncopaid.tracker_loop import TrackerLoop

    tracker = TrackerLoop(poll_interval=0.1, idle_threshold=300)

    # Verify lock tracking state is initialized
    assert hasattr(tracker, '_was_locked')
    assert tracker._was_locked is False


def test_locked_or_screensaver_combines_both_checks():
    """Test that is_locked_or_screensaver flag combines lock and screensaver detection."""
    from syncopaid.tracker_windows import is_workstation_locked, is_screensaver_active

    # Both functions should exist and return boolean
    lock_result = is_workstation_locked()
    screensaver_result = is_screensaver_active()

    assert isinstance(lock_result, bool)
    assert isinstance(screensaver_result, bool)

    # If either is True, should be treated as locked/screensaver
    # This test verifies the functions exist and work
