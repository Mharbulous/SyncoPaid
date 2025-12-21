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


def test_get_active_window_includes_cmdline():
    from syncopaid.tracker_windows import get_active_window

    with patch('syncopaid.tracker_windows.WINDOWS_APIS_AVAILABLE', False):
        result = get_active_window()

    assert 'cmdline' in result


def test_tracker_loop_includes_cmdline_in_event():
    from syncopaid.tracker import TrackerLoop, ActivityEvent

    tracker = TrackerLoop(poll_interval=0.01, idle_threshold=180.0)

    windows = [
        {'app': 'chrome.exe', 'title': 'Tab1', 'pid': 1234, 'cmdline': ['chrome.exe', '--profile-directory=Work']},
        {'app': 'notepad.exe', 'title': 'Document', 'pid': 5678, 'cmdline': ['notepad.exe']},
    ]
    call_count = [0]

    def mock_window():
        idx = min(call_count[0], len(windows) - 1)
        call_count[0] += 1
        return windows[idx]

    with patch('syncopaid.tracker_loop.get_active_window', side_effect=mock_window):
        with patch('syncopaid.tracker_loop.get_idle_seconds', return_value=0.0):
            with patch('syncopaid.tracker_loop.is_workstation_locked', return_value=False):
                with patch('syncopaid.tracker_loop.is_screensaver_active', return_value=False):
                    with patch('syncopaid.tracker_loop.submit_screenshot'):
                        with patch('time.sleep'):
                            gen = tracker.start()
                            events = []
                            for i, event in enumerate(gen):
                                if isinstance(event, ActivityEvent):
                                    events.append(event)
                                if i >= 10:
                                    tracker.stop()
                                    break

    activity_events = [e for e in events if isinstance(e, ActivityEvent)]
    assert len(activity_events) > 0, f"No activity events found. Events: {events}"
    assert activity_events[0].cmdline == ['chrome.exe', '--profile-directory=Work'], f"Expected cmdline ['chrome.exe', '--profile-directory=Work'], got {activity_events[0].cmdline}"


def test_database_cmdline_column_exists():
    from syncopaid.database import Database
    import sqlite3
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert 'cmdline' in columns


def test_database_insert_event_with_cmdline():
    from syncopaid.database import Database
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00+00:00",
            duration_seconds=60.0,
            app="chrome.exe",
            title="Test",
            cmdline=["chrome.exe", "--profile-directory=Work"]
        )

        db.insert_event(event)
        events = db.get_events()

        assert len(events) == 1
        assert 'cmdline' in events[0]
        assert '"--profile-directory=Work"' in events[0]['cmdline']


if __name__ == "__main__":
    test_activity_event_has_cmdline_field()
    test_activity_event_cmdline_defaults_to_none()
    test_activity_event_to_dict_includes_cmdline()
    test_get_process_cmdline_returns_list()
    test_get_process_cmdline_handles_access_denied()
    test_redact_sensitive_paths_preserves_profile()
    test_redact_sensitive_paths_redacts_file_paths()
    test_get_active_window_includes_cmdline()
    test_tracker_loop_includes_cmdline_in_event()
    test_database_cmdline_column_exists()
    test_database_insert_event_with_cmdline()
    print("All tests passed!")
