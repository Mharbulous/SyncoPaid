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
