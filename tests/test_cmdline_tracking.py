"""Tests for process command line tracking functionality."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from syncopaid.tracker import ActivityEvent
from unittest.mock import patch, MagicMock


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


def test_get_process_cmdline_returns_list():
    from syncopaid.tracker_windows import get_process_cmdline, WINDOWS_APIS_AVAILABLE

    if not WINDOWS_APIS_AVAILABLE:
        # On non-Windows or when APIs are unavailable, should return None
        result = get_process_cmdline(1234)
        assert result is None
        return

    import psutil
    mock_process = MagicMock()
    mock_process.cmdline.return_value = ["chrome.exe", "--profile-directory=Default"]

    with patch('psutil.Process', return_value=mock_process):
        result = get_process_cmdline(1234)

    assert result == ["chrome.exe", "--profile-directory=Default"]


def test_get_process_cmdline_handles_access_denied():
    from syncopaid.tracker_windows import get_process_cmdline, WINDOWS_APIS_AVAILABLE

    if not WINDOWS_APIS_AVAILABLE:
        # On non-Windows, should return None
        result = get_process_cmdline(1234)
        assert result is None
        return

    import psutil

    with patch('psutil.Process', side_effect=psutil.AccessDenied()):
        result = get_process_cmdline(1234)

    assert result is None


def test_redact_sensitive_paths_preserves_profile():
    from syncopaid.tracker_windows import redact_sensitive_paths
    cmdline = ["chrome.exe", "--profile-directory=Work", "--flag"]
    result = redact_sensitive_paths(cmdline)
    assert "--profile-directory=Work" in result


def test_redact_sensitive_paths_redacts_file_paths():
    from syncopaid.tracker_windows import redact_sensitive_paths
    cmdline = ["WINWORD.EXE", "C:\\Users\\Brahm\\Documents\\secret.docx"]
    result = redact_sensitive_paths(cmdline)
    assert "Brahm" not in str(result)
    assert "secret.docx" in str(result)


if __name__ == "__main__":
    test_activity_event_has_cmdline_field()
    test_activity_event_cmdline_defaults_to_none()
    test_activity_event_to_dict_includes_cmdline()
    test_get_process_cmdline_returns_list()
    test_get_process_cmdline_handles_access_denied()
    test_redact_sensitive_paths_preserves_profile()
    test_redact_sensitive_paths_redacts_file_paths()
    print("All tests passed!")
