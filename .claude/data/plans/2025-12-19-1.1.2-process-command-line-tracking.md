# Process Command Line and Arguments Tracking - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Capture process command line arguments to distinguish between multiple instances of the same application (e.g., multiple Chrome profiles, multiple Word documents)
**Approach:** Extend `get_active_window()` to capture command line via psutil, add `cmdline` field to `ActivityEvent`, update database schema with migration, redact sensitive paths for privacy
**Tech Stack:** psutil (already installed), sqlite3, Python dataclasses

---

**Story ID:** 1.1.2 | **Created:** 2025-12-19 | **Stage:** `planned`

---

## Story Context

**Title:** Process Command Line and Arguments Tracking

**Description:** Current `get_active_window()` (tracker.py:149-191) captures process name via psutil but not cmdline. Multiple instances of same app (chrome.exe, WINWORD.EXE) look identical without cmdline context. Vision: "Context-Aware Categorization: capture rich contextual data" - cmdline provides instance-level context. Common lawyer workflow: multiple Chrome profiles (work vs personal), multiple documents open.

**Acceptance Criteria:**
- [ ] `get_active_window()` captures process command line arguments
- [ ] `ActivityEvent` dataclass includes new `cmdline` field
- [ ] Database schema adds `cmdline` column with migration for existing databases
- [ ] Sensitive paths are redacted before storage (privacy protection)
- [ ] Multiple instances of same app are distinguishable by cmdline

**Notes:** Check for duplicative stories before implementation

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Add cmdline Field to ActivityEvent Dataclass (~3 min)

**Files:**
- **Create:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/tracker.py:87-117`

**Context:** The ActivityEvent dataclass is the core data structure that represents captured activities. Adding a `cmdline` field here enables command line data to flow through the entire system.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py
"""Tests for process command line tracking functionality."""

import pytest
from syncopaid.tracker import ActivityEvent


def test_activity_event_has_cmdline_field():
    """Verify ActivityEvent dataclass includes optional cmdline field."""
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
    """Verify cmdline field defaults to None for backward compatibility."""
    event = ActivityEvent(
        timestamp="2025-12-19T10:00:00+00:00",
        duration_seconds=60.0,
        app="chrome.exe",
        title="Google - Google Chrome"
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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_activity_event_has_cmdline_field -v
```
Expected output: `FAILED` (ActivityEvent does not have cmdline field)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (lines 87-117)
# Find the ActivityEvent dataclass and add cmdline field after url field:

@dataclass
class ActivityEvent:
    """
    Represents a single captured activity event.

    This is the core data structure that will be stored in the database
    and exported for LLM processing.

    Fields:
        timestamp: Start time in ISO8601 format (e.g., "2025-12-09T10:30:45")
        duration_seconds: Duration in seconds (may be None for legacy records)
        end_time: End time in ISO8601 format (may be None for legacy records)
        app: Application executable name
        title: Window title
        url: URL if applicable (future enhancement)
        cmdline: Process command line arguments (for distinguishing app instances)
        is_idle: Whether this was an idle period (deprecated - use state)
        state: Activity state or client matter number (e.g., "Active", "1023.L213")
    """
    timestamp: str  # ISO8601 format: "2025-12-09T10:30:45" (start time)
    duration_seconds: Optional[float]
    app: Optional[str]
    title: Optional[str]
    end_time: Optional[str] = None  # ISO8601 format (end time)
    url: Optional[str] = None
    cmdline: Optional[List[str]] = None  # Process command line arguments
    is_idle: bool = False
    state: str = STATE_ACTIVE  # Default to Active (client matter TBD)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export or database storage."""
        return asdict(self)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py -v
```
Expected output: `PASSED` (all 3 tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/tracker.py && git commit -m "feat(tracker): add cmdline field to ActivityEvent dataclass"
```

---

### Task 2: Implement get_process_cmdline Helper Function (~4 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/tracker.py:191-220`

**Context:** We need a helper function that safely extracts command line from a process ID. This handles errors gracefully (AccessDenied, NoSuchProcess) and returns None when extraction fails.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)
from unittest.mock import patch, MagicMock


def test_get_process_cmdline_returns_list():
    """Verify get_process_cmdline returns command line as list."""
    from syncopaid.tracker import get_process_cmdline

    # Mock psutil.Process to return a command line
    mock_process = MagicMock()
    mock_process.cmdline.return_value = ["chrome.exe", "--profile-directory=Default"]

    with patch('syncopaid.tracker.psutil.Process', return_value=mock_process):
        result = get_process_cmdline(1234)

    assert result == ["chrome.exe", "--profile-directory=Default"]


def test_get_process_cmdline_handles_access_denied():
    """Verify get_process_cmdline returns None on AccessDenied."""
    from syncopaid.tracker import get_process_cmdline
    import psutil

    with patch('syncopaid.tracker.psutil.Process', side_effect=psutil.AccessDenied()):
        result = get_process_cmdline(1234)

    assert result is None


def test_get_process_cmdline_handles_no_such_process():
    """Verify get_process_cmdline returns None on NoSuchProcess."""
    from syncopaid.tracker import get_process_cmdline
    import psutil

    with patch('syncopaid.tracker.psutil.Process', side_effect=psutil.NoSuchProcess(1234)):
        result = get_process_cmdline(1234)

    assert result is None


def test_get_process_cmdline_handles_empty_cmdline():
    """Verify get_process_cmdline returns None for empty command line."""
    from syncopaid.tracker import get_process_cmdline

    mock_process = MagicMock()
    mock_process.cmdline.return_value = []

    with patch('syncopaid.tracker.psutil.Process', return_value=mock_process):
        result = get_process_cmdline(1234)

    assert result is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_get_process_cmdline_returns_list -v
```
Expected output: `FAILED` (get_process_cmdline does not exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (add after get_idle_seconds function, around line 217)

def get_process_cmdline(pid: int) -> Optional[List[str]]:
    """
    Get the command line arguments for a process by PID.

    This provides instance-level context for distinguishing between
    multiple instances of the same application (e.g., Chrome profiles).

    Args:
        pid: Process ID to query

    Returns:
        List of command line arguments, or None if unavailable/empty.
    """
    if not WINDOWS_APIS_AVAILABLE:
        return None

    try:
        process = psutil.Process(pid)
        cmdline = process.cmdline()
        return cmdline if cmdline else None
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
        return None
    except Exception as e:
        logging.debug(f"Error getting cmdline for PID {pid}: {e}")
        return None
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_get_process_cmdline_returns_list tests/test_cmdline_tracking.py::test_get_process_cmdline_handles_access_denied tests/test_cmdline_tracking.py::test_get_process_cmdline_handles_no_such_process tests/test_cmdline_tracking.py::test_get_process_cmdline_handles_empty_cmdline -v
```
Expected output: `PASSED` (all 4 tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/tracker.py && git commit -m "feat(tracker): add get_process_cmdline helper function"
```

---

### Task 3: Implement Path Redaction for Privacy (~4 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/tracker.py:220-260`

**Context:** Command line arguments may contain sensitive file paths (client names, matter numbers in paths). We must redact these before storage to protect attorney-client privilege while preserving useful context like profile names.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)

def test_redact_sensitive_paths_preserves_profile():
    """Verify profile directory flags are preserved."""
    from syncopaid.tracker import redact_sensitive_paths

    cmdline = ["chrome.exe", "--profile-directory=Work", "--flag"]
    result = redact_sensitive_paths(cmdline)

    assert "--profile-directory=Work" in result


def test_redact_sensitive_paths_redacts_file_paths():
    """Verify file paths are redacted to protect client data."""
    from syncopaid.tracker import redact_sensitive_paths

    cmdline = [
        "WINWORD.EXE",
        "C:\\Users\\Brahm\\Documents\\ClientA\\MatterX\\contract.docx"
    ]
    result = redact_sensitive_paths(cmdline)

    # Should redact the path but preserve the filename
    assert "ClientA" not in str(result)
    assert "contract.docx" in str(result)


def test_redact_sensitive_paths_handles_user_paths():
    """Verify user-specific paths are redacted."""
    from syncopaid.tracker import redact_sensitive_paths

    cmdline = [
        "notepad.exe",
        "C:\\Users\\JohnSmith\\Desktop\\notes.txt"
    ]
    result = redact_sensitive_paths(cmdline)

    # Should redact username but preserve filename
    assert "JohnSmith" not in str(result)
    assert "notes.txt" in str(result)


def test_redact_sensitive_paths_preserves_flags():
    """Verify command line flags are preserved unchanged."""
    from syncopaid.tracker import redact_sensitive_paths

    cmdline = ["app.exe", "--verbose", "-n", "5", "--config=default"]
    result = redact_sensitive_paths(cmdline)

    assert result == cmdline  # Flags should be unchanged
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_redact_sensitive_paths_preserves_profile -v
```
Expected output: `FAILED` (redact_sensitive_paths does not exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (add after get_process_cmdline function)

def redact_sensitive_paths(cmdline: List[str]) -> List[str]:
    """
    Redact sensitive file paths from command line arguments.

    Preserves useful context (profile names, flags) while protecting
    potentially sensitive information (client names in paths, usernames).

    Redaction rules:
    - File paths: Keep only the filename, redact directory structure
    - User paths: Replace username with [USER]
    - Profile flags (--profile-directory=X): Preserve as-is (useful context)
    - Regular flags (--verbose, -n, etc.): Preserve as-is

    Args:
        cmdline: List of command line arguments

    Returns:
        List with sensitive paths redacted
    """
    if not cmdline:
        return []

    import re
    import os

    result = []
    # Pattern to detect Windows file paths
    path_pattern = re.compile(r'^[A-Za-z]:\\')
    # Pattern to detect user directories
    user_pattern = re.compile(r'\\Users\\[^\\]+\\', re.IGNORECASE)

    for arg in cmdline:
        # Skip empty arguments
        if not arg:
            continue

        # Preserve profile directory flags (useful for distinguishing Chrome instances)
        if arg.startswith('--profile-directory=') or arg.startswith('--profile='):
            result.append(arg)
            continue

        # Check if argument looks like a file path
        if path_pattern.match(arg):
            # Extract just the filename
            filename = os.path.basename(arg)
            # Check if path contains user directory
            if user_pattern.search(arg):
                result.append(f"[REDACTED_PATH]\\{filename}")
            else:
                result.append(f"[PATH]\\{filename}")
            continue

        # Preserve other arguments as-is (flags, options, etc.)
        result.append(arg)

    return result
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_redact_sensitive_paths_preserves_profile tests/test_cmdline_tracking.py::test_redact_sensitive_paths_redacts_file_paths tests/test_cmdline_tracking.py::test_redact_sensitive_paths_handles_user_paths tests/test_cmdline_tracking.py::test_redact_sensitive_paths_preserves_flags -v
```
Expected output: `PASSED` (all 4 tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/tracker.py && git commit -m "feat(tracker): add redact_sensitive_paths for privacy protection"
```

---

### Task 4: Update get_active_window to Capture cmdline (~4 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/tracker.py:149-191`

**Context:** The `get_active_window()` function is called every poll interval (1 second). It currently returns app, title, and pid. We need to also capture and return the command line (redacted).

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)

def test_get_active_window_includes_cmdline():
    """Verify get_active_window returns cmdline in result dict."""
    from syncopaid.tracker import get_active_window

    with patch('syncopaid.tracker.WINDOWS_APIS_AVAILABLE', False):
        result = get_active_window()

    # Mock data should include cmdline key (even if None for mock)
    assert 'cmdline' in result


def test_get_active_window_cmdline_is_redacted():
    """Verify get_active_window returns redacted cmdline."""
    from syncopaid.tracker import get_active_window

    # Mock the Windows APIs
    mock_hwnd = 12345
    mock_title = "Document.docx - Word"
    mock_pid = 9999
    mock_cmdline = ["WINWORD.EXE", "C:\\Users\\Brahm\\Docs\\secret.docx"]

    with patch('syncopaid.tracker.WINDOWS_APIS_AVAILABLE', True):
        with patch('syncopaid.tracker.win32gui') as mock_win32gui:
            with patch('syncopaid.tracker.win32process') as mock_win32process:
                with patch('syncopaid.tracker.psutil') as mock_psutil:
                    mock_win32gui.GetForegroundWindow.return_value = mock_hwnd
                    mock_win32gui.GetWindowText.return_value = mock_title
                    mock_win32process.GetWindowThreadProcessId.return_value = (0, mock_pid)

                    mock_process = MagicMock()
                    mock_process.name.return_value = "WINWORD.EXE"
                    mock_process.cmdline.return_value = mock_cmdline
                    mock_psutil.Process.return_value = mock_process

                    result = get_active_window()

    # Cmdline should be present and redacted
    assert result['cmdline'] is not None
    assert "secret.docx" in str(result['cmdline'])  # Filename preserved
    assert "Brahm" not in str(result['cmdline'])  # Username redacted
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_get_active_window_includes_cmdline -v
```
Expected output: `FAILED` (get_active_window does not return cmdline key)

**Step 3 - GREEN:** Modify get_active_window function
```python
# src/syncopaid/tracker.py (lines 149-191)
# Replace the get_active_window function:

def get_active_window() -> Dict[str, Optional[str]]:
    """
    Get information about the currently active foreground window.

    Returns:
        Dictionary with keys:
        - 'app': Executable name (e.g., 'WINWORD.EXE', 'chrome.exe')
        - 'title': Window title text
        - 'pid': Process ID (for debugging)
        - 'cmdline': Redacted command line arguments (for instance differentiation)

    Note: Returns mock data on non-Windows platforms for testing.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock data for testing on non-Windows platforms
        import random
        mock_apps = [
            ("WINWORD.EXE", "Smith-Contract-v2.docx - Word", ["WINWORD.EXE", "[PATH]\\Smith-Contract-v2.docx"]),
            ("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome", ["chrome.exe", "--profile-directory=Default"]),
            ("OUTLOOK.EXE", "Inbox - user@lawfirm.com - Outlook", ["OUTLOOK.EXE"]),
        ]
        app, title, cmdline = random.choice(mock_apps)
        return {"app": app, "title": title, "pid": 0, "cmdline": cmdline}

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Handle signed/unsigned integer overflow from Windows API
        # Windows returns unsigned 32-bit PID, but Python may interpret as signed
        if pid < 0:
            pid = pid & 0xFFFFFFFF  # Convert to unsigned

        process_name = None
        cmdline = None

        try:
            process = psutil.Process(pid)
            process_name = process.name()
            raw_cmdline = process.cmdline()
            if raw_cmdline:
                cmdline = redact_sensitive_paths(raw_cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            pass

        return {"app": process_name, "title": title, "pid": pid, "cmdline": cmdline}

    except Exception as e:
        logging.error(f"Error getting active window: {e}")
        return {"app": None, "title": None, "pid": None, "cmdline": None}
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_get_active_window_includes_cmdline tests/test_cmdline_tracking.py::test_get_active_window_cmdline_is_redacted -v
```
Expected output: `PASSED` (both tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/tracker.py && git commit -m "feat(tracker): capture redacted cmdline in get_active_window"
```

---

### Task 5: Update TrackerLoop to Include cmdline in State (~3 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/tracker.py:340-380` and `src/syncopaid/tracker.py:430-460`

**Context:** The TrackerLoop's internal state dictionary and `_finalize_current_event` method need to include cmdline so it flows through to the ActivityEvent.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)

def test_tracker_loop_includes_cmdline_in_event():
    """Verify TrackerLoop yields events with cmdline field populated."""
    from syncopaid.tracker import TrackerLoop, ActivityEvent

    tracker = TrackerLoop(poll_interval=0.01, idle_threshold=180.0)

    # Mock windows with cmdline
    windows = [
        {'app': 'chrome.exe', 'title': 'Tab1', 'pid': 1234, 'cmdline': ['chrome.exe', '--profile-directory=Work']},
        {'app': 'chrome.exe', 'title': 'Tab2', 'pid': 1234, 'cmdline': ['chrome.exe', '--profile-directory=Work']},
    ]
    call_count = [0]

    def mock_window():
        idx = min(call_count[0], len(windows) - 1)
        call_count[0] += 1
        return windows[idx]

    with patch('syncopaid.tracker.get_active_window', side_effect=mock_window):
        with patch('syncopaid.tracker.get_idle_seconds', return_value=0.0):
            with patch('time.sleep'):
                gen = tracker.start()
                # Get first event (triggered by title change)
                events = []
                for i, event in enumerate(gen):
                    if isinstance(event, ActivityEvent):
                        events.append(event)
                    if i >= 3:
                        tracker.stop()
                        break

    # At least one event should have cmdline
    activity_events = [e for e in events if isinstance(e, ActivityEvent)]
    assert len(activity_events) > 0
    assert activity_events[0].cmdline == ['chrome.exe', '--profile-directory=Work']
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_tracker_loop_includes_cmdline_in_event -v
```
Expected output: `FAILED` (ActivityEvent.cmdline is None or missing)

**Step 3 - GREEN:** Modify TrackerLoop to include cmdline

First, update the state dictionary creation (around line 343-347):
```python
# src/syncopaid/tracker.py (around line 343-347)
# In the start() method, update the state dict to include cmdline:

                # Create state dict for comparison
                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'is_idle': is_idle,
                    'cmdline': window.get('cmdline')  # Add cmdline to state
                }
```

Then, update _finalize_current_event (around line 451-459):
```python
# src/syncopaid/tracker.py (around line 451-459)
# In _finalize_current_event(), add cmdline to the ActivityEvent:

        # Create event with start time, duration, end time, and state
        event = ActivityEvent(
            timestamp=self.event_start_time.isoformat(),
            duration_seconds=round(duration, 2),
            app=self.current_event['app'],
            title=self.current_event['title'],
            end_time=end_time.isoformat(),
            url=None,  # URL extraction is future enhancement
            cmdline=self.current_event.get('cmdline'),  # Add cmdline
            is_idle=self.current_event['is_idle'],
            state=event_state
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_tracker_loop_includes_cmdline_in_event -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/tracker.py && git commit -m "feat(tracker): propagate cmdline through TrackerLoop to ActivityEvent"
```

---

### Task 6: Add cmdline Column to Database Schema (~4 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/database.py:67-142`

**Context:** The database needs a new `cmdline` column to persist command line data. We need a migration for existing databases and must update insert/query methods.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)
import tempfile
import os


def test_database_cmdline_column_exists():
    """Verify database schema includes cmdline column."""
    from syncopaid.database import Database

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        # Check schema has cmdline column
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert 'cmdline' in columns


def test_database_insert_event_with_cmdline():
    """Verify insert_event stores cmdline field."""
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

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

        event_id = db.insert_event(event)

        # Query and verify
        events = db.get_events()
        assert len(events) == 1
        assert events[0]['cmdline'] == '["chrome.exe", "--profile-directory=Work"]'


def test_database_get_events_returns_cmdline():
    """Verify get_events returns cmdline in results."""
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00+00:00",
            duration_seconds=60.0,
            app="chrome.exe",
            title="Test",
            cmdline=["chrome.exe", "--profile-directory=Personal"]
        )

        db.insert_event(event)
        events = db.get_events()

        assert 'cmdline' in events[0]
        assert events[0]['cmdline'] is not None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_database_cmdline_column_exists -v
```
Expected output: `FAILED` (cmdline column does not exist)

**Step 3 - GREEN:** Update database schema and methods
```python
# src/syncopaid/database.py

# 1. Update _init_schema (around line 67-142) to add cmdline column and migration:

    def _init_schema(self):
        """
        Create database schema if it doesn't exist.

        Schema includes:
        - events table with all activity fields
        - screenshots table with captured screenshots metadata
        - Indices on timestamp and app for query performance
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL,
                    end_time TEXT,
                    app TEXT,
                    title TEXT,
                    url TEXT,
                    cmdline TEXT,
                    is_idle INTEGER DEFAULT 0
                )
            """)

            # Migration: Add end_time column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(events)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'end_time' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN end_time TEXT")
                logging.info("Database migration: Added end_time column to events table")

            # Migration: Add state column if it doesn't exist
            if 'state' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN state TEXT DEFAULT 'Active'")
                logging.info("Database migration: Added state column to events table")

                # Backfill existing data: set state based on is_idle
                cursor.execute("""
                    UPDATE events
                    SET state = CASE WHEN is_idle = 1 THEN 'Inactive' ELSE 'Active' END
                    WHERE state IS NULL
                """)
                logging.info("Database migration: Backfilled state column from is_idle")

            # Migration: Add cmdline column if it doesn't exist
            # Re-fetch columns after potential migrations above
            cursor.execute("PRAGMA table_info(events)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'cmdline' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN cmdline TEXT")
                logging.info("Database migration: Added cmdline column to events table")

            # ... rest of schema init (indices, screenshots table) remains unchanged ...
```

```python
# 2. Update insert_event (around line 144-175) to include cmdline:

    def insert_event(self, event: ActivityEvent) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store

        Returns:
            The ID of the inserted event
        """
        import json

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')

            # Serialize cmdline list to JSON string for storage
            cmdline = getattr(event, 'cmdline', None)
            cmdline_json = json.dumps(cmdline) if cmdline else None

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline, is_idle, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                cmdline_json,
                1 if event.is_idle else 0,
                state
            ))

            return cursor.lastrowid
```

```python
# 3. Update get_events (around line 250-272) to include cmdline in results:

            # Convert rows to dictionaries
            events = []
            for row in cursor.fetchall():
                # Derive state from is_idle if column doesn't exist (backward compatibility)
                if 'state' in row.keys() and row['state']:
                    state = row['state']
                else:
                    state = 'Inactive' if row['is_idle'] else 'Active'

                # Get cmdline (may be None for legacy records)
                cmdline = row['cmdline'] if 'cmdline' in row.keys() else None

                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'duration_seconds': row['duration_seconds'],
                    'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                    'app': row['app'],
                    'title': row['title'],
                    'url': row['url'],
                    'cmdline': cmdline,
                    'is_idle': bool(row['is_idle']),
                    'state': state
                })

            return events
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_database_cmdline_column_exists tests/test_cmdline_tracking.py::test_database_insert_event_with_cmdline tests/test_cmdline_tracking.py::test_database_get_events_returns_cmdline -v
```
Expected output: `PASSED` (all 3 tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/database.py && git commit -m "feat(database): add cmdline column with migration support"
```

---

### Task 7: Update insert_events_batch for cmdline (~2 min)

**Files:**
- **Modify:** `tests/test_cmdline_tracking.py`
- **Modify:** `src/syncopaid/database.py:177-202`

**Context:** The batch insert method also needs to serialize cmdline to JSON for consistency.

**Step 1 - RED:** Write failing test
```python
# tests/test_cmdline_tracking.py (append to existing file)

def test_database_insert_events_batch_with_cmdline():
    """Verify insert_events_batch stores cmdline for multiple events."""
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        events = [
            ActivityEvent(
                timestamp="2025-12-19T10:00:00+00:00",
                duration_seconds=60.0,
                app="chrome.exe",
                title="Tab1",
                cmdline=["chrome.exe", "--profile-directory=Work"]
            ),
            ActivityEvent(
                timestamp="2025-12-19T10:01:00+00:00",
                duration_seconds=60.0,
                app="chrome.exe",
                title="Tab2",
                cmdline=["chrome.exe", "--profile-directory=Personal"]
            )
        ]

        db.insert_events_batch(events)
        results = db.get_events()

        assert len(results) == 2
        assert '"--profile-directory=Work"' in results[0]['cmdline']
        assert '"--profile-directory=Personal"' in results[1]['cmdline']
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_cmdline_tracking.py::test_database_insert_events_batch_with_cmdline -v
```
Expected output: `FAILED` (cmdline not being stored in batch insert)

**Step 3 - GREEN:** Update insert_events_batch
```python
# src/syncopaid/database.py (around line 177-202)

    def insert_events_batch(self, events: List[ActivityEvent]) -> int:
        """
        Insert multiple events in a single transaction (more efficient).

        Args:
            events: List of ActivityEvent objects

        Returns:
            Number of events inserted
        """
        import json

        if not events:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, cmdline, is_idle, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url,
                 json.dumps(getattr(e, 'cmdline', None)) if getattr(e, 'cmdline', None) else None,
                 1 if e.is_idle else 0, getattr(e, 'state', 'Active'))
                for e in events
            ])

            return len(events)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_cmdline_tracking.py::test_database_insert_events_batch_with_cmdline -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_cmdline_tracking.py src/syncopaid/database.py && git commit -m "feat(database): add cmdline support to batch insert"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid.tracker            # Module runs without error (30s test)
python -m syncopaid.database           # Database module runs without error
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- Command line data is stored as JSON string in SQLite (list serialization)
- Path redaction is aggressive to protect attorney-client privilege
- Profile directory flags are preserved as they're useful for AI categorization
- Empty command lines are stored as NULL (not empty string or empty array)
- Existing databases will get the `cmdline` column via auto-migration on first access
- The `cmdline` field in ActivityEvent uses `List[str]` type but database stores as JSON string
