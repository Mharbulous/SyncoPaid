# Window Interaction Level Detection - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Detect and track interaction levels (typing, clicking, passive reading) in addition to global idle detection, enabling more granular time attribution for lawyers.
**Approach:** Extend `tracker.py` to track last typing time and last click time using Windows `GetAsyncKeyState` polling, then calculate interaction age to classify activity as "typing", "clicking", or "passive". Store interaction level in `ActivityEvent` for billing categorization.
**Tech Stack:** pywin32 (`ctypes.windll.user32`), existing tracker.py infrastructure

---

**Story ID:** 1.1.3 | **Created:** 2025-12-19 | **Stage:** `planned`

---

## Story Context

**Title:** Window Interaction Level Detection
**Description:** Current idle detection (tracker.py:174-197) uses GetLastInputInfo to detect global user activity, but doesn't distinguish between active typing in Word vs passive reading of a PDF. Lawyers need granular time attribution: 15 minutes reading a contract should be billable but categorized differently than 15 minutes drafting a motion.

**Acceptance Criteria:**
- [ ] Track last typing time separately from last click time
- [ ] Calculate interaction age to classify activity type
- [ ] Add interaction_level field to ActivityEvent (typing/clicking/passive/idle)
- [ ] Store interaction level in database events table
- [ ] Privacy: Only capture interaction timing, never keystroke content

**Notes:** This enhancement enables the AI categorization to distinguish between drafting, reviewing, and passive reference activities.

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Add InteractionLevel Enum and ActivityEvent Field (~3 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py:40-60` (add enum after STATE constants)
- **Modify:** `src/syncopaid/tracker.py:88-117` (add field to ActivityEvent)
- **Create:** `tests/test_interaction_level.py`

**Context:** We need to define the possible interaction levels as an enum for type safety and add a field to ActivityEvent. The enum values represent the lawyer's interaction intensity with the window.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py
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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py -v
```
Expected output: `FAILED` (test should fail because InteractionLevel doesn't exist yet)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (add after line 59, before line 60 "# Client matter pattern")
from enum import Enum

class InteractionLevel(Enum):
    """
    Represents the level of user interaction with a window.

    Values:
        TYPING: User is actively typing (keyboard input within threshold)
        CLICKING: User is clicking (mouse input within threshold, no recent typing)
        PASSIVE: Window is active but no recent input (reading/reference)
        IDLE: Global idle detected (away from computer)
    """
    TYPING = "typing"
    CLICKING = "clicking"
    PASSIVE = "passive"
    IDLE = "idle"
```

```python
# src/syncopaid/tracker.py (modify ActivityEvent dataclass, add field after state)
# Around line 113, add new field before to_dict method:
    interaction_level: str = InteractionLevel.PASSIVE.value  # Default to passive
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/tracker.py && git commit -m "feat: add InteractionLevel enum and ActivityEvent field"
```

---

### Task 2: Add Keyboard/Mouse State Detection Functions (~4 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py:143-218` (add after get_idle_seconds function)
- **Modify:** `tests/test_interaction_level.py` (add new tests)

**Context:** We need Windows API functions to detect keyboard and mouse activity. We'll use `GetAsyncKeyState` to check if any key/mouse button was recently pressed. The privacy note specifies we only capture timing, never actual keystroke content.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_is_key_pressed_returns_bool tests/test_interaction_level.py::test_get_keyboard_activity_returns_bool tests/test_interaction_level.py::test_get_mouse_activity_returns_bool -v
```
Expected output: `FAILED` (functions don't exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (add after get_idle_seconds function, around line 218)

def is_key_pressed(vk_code: int) -> bool:
    """
    Check if a specific virtual key is currently pressed.

    Uses GetAsyncKeyState to check key state without blocking.
    Privacy note: Only checks if key is pressed, never captures which key.

    Args:
        vk_code: Windows virtual key code

    Returns:
        True if key is currently pressed, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    try:
        # High-order bit indicates key is currently pressed
        return bool(windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
    except Exception:
        return False


def get_keyboard_activity() -> bool:
    """
    Check if any keyboard key is currently being pressed.

    Checks a range of common keys to detect typing activity.
    Privacy note: Only detects activity, never captures content.

    Returns:
        True if any typing activity detected, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    # Check alphanumeric keys (0x30-0x5A covers 0-9, A-Z)
    for vk in range(0x30, 0x5B):
        if is_key_pressed(vk):
            return True

    # Check common punctuation/editing keys
    editing_keys = [
        0x08,  # Backspace
        0x09,  # Tab
        0x0D,  # Enter
        0x20,  # Space
        0xBA,  # Semicolon
        0xBB,  # Equals
        0xBC,  # Comma
        0xBD,  # Minus
        0xBE,  # Period
        0xBF,  # Slash
    ]
    for vk in editing_keys:
        if is_key_pressed(vk):
            return True

    return False


def get_mouse_activity() -> bool:
    """
    Check if any mouse button is currently being pressed.

    Checks left, right, and middle mouse buttons.

    Returns:
        True if any mouse button is pressed, False otherwise
    """
    if not WINDOWS_APIS_AVAILABLE:
        return False

    # Virtual key codes for mouse buttons
    mouse_buttons = [
        0x01,  # VK_LBUTTON (left)
        0x02,  # VK_RBUTTON (right)
        0x04,  # VK_MBUTTON (middle)
    ]

    for vk in mouse_buttons:
        if is_key_pressed(vk):
            return True

    return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_is_key_pressed_returns_bool tests/test_interaction_level.py::test_get_keyboard_activity_returns_bool tests/test_interaction_level.py::test_get_mouse_activity_returns_bool -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/tracker.py && git commit -m "feat: add keyboard/mouse activity detection functions"
```

---

### Task 3: Add Interaction Tracking State to TrackerLoop (~3 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py:243-270` (TrackerLoop.__init__)
- **Modify:** `tests/test_interaction_level.py` (add new tests)

**Context:** TrackerLoop needs to track when the user last typed and last clicked to calculate interaction age. We add state variables for this tracking, with a configurable threshold for how long activity is considered "recent".

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_tracker_loop_has_interaction_tracking_state tests/test_interaction_level.py::test_tracker_loop_default_interaction_threshold -v
```
Expected output: `FAILED` (TrackerLoop doesn't have these attributes)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (modify TrackerLoop.__init__, around line 243-257)
# Add parameter to __init__ signature and state variables

    def __init__(
        self,
        poll_interval: float = 1.0,
        idle_threshold: float = 180.0,
        merge_threshold: float = 2.0,
        screenshot_worker=None,
        screenshot_interval: float = 10.0,
        minimum_idle_duration: float = 180.0,
        interaction_threshold: float = 5.0  # NEW: seconds before interaction considered stale
    ):
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.merge_threshold = merge_threshold
        self.screenshot_worker = screenshot_worker
        self.screenshot_interval = screenshot_interval
        self.minimum_idle_duration = minimum_idle_duration
        self.interaction_threshold = interaction_threshold  # NEW

        # State tracking for event merging
        self.current_event: Optional[Dict] = None
        self.event_start_time: Optional[datetime] = None

        # Idle resumption tracking
        self.was_idle: bool = False
        self.last_idle_resumption_time: Optional[datetime] = None

        # Interaction level tracking (NEW)
        self.last_typing_time: Optional[datetime] = None
        self.last_click_time: Optional[datetime] = None

        # Screenshot timing
        self.last_screenshot_time: float = 0

        self.running = False

        # Statistics
        self.total_events = 0
        self.merged_events = 0
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_tracker_loop_has_interaction_tracking_state tests/test_interaction_level.py::test_tracker_loop_default_interaction_threshold -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/tracker.py && git commit -m "feat: add interaction tracking state to TrackerLoop"
```

---

### Task 4: Add get_interaction_level Method (~4 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py` (add method to TrackerLoop class)
- **Modify:** `tests/test_interaction_level.py` (add new tests)

**Context:** We need a method that checks current keyboard/mouse activity, updates tracking timestamps, and returns the current interaction level. This encapsulates the classification logic.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

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
    with patch('syncopaid.tracker.get_keyboard_activity', return_value=False):
        with patch('syncopaid.tracker.get_mouse_activity', return_value=False):
            level = tracker.get_interaction_level(idle_seconds=0.0)

    # With no recent activity, should be PASSIVE
    assert level == InteractionLevel.PASSIVE
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_get_interaction_level_returns_idle_when_globally_idle tests/test_interaction_level.py::test_get_interaction_level_returns_passive_when_no_activity -v
```
Expected output: `FAILED` (get_interaction_level method doesn't exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (add method to TrackerLoop class, after __init__)

    def get_interaction_level(self, idle_seconds: float) -> InteractionLevel:
        """
        Determine current interaction level based on activity state.

        Updates internal tracking timestamps when activity is detected.

        Priority order:
        1. IDLE if globally idle (idle_seconds >= idle_threshold)
        2. TYPING if keyboard activity detected or recent
        3. CLICKING if mouse activity detected or recent
        4. PASSIVE if none of the above

        Args:
            idle_seconds: Current global idle time from GetLastInputInfo

        Returns:
            InteractionLevel enum value
        """
        now = datetime.now(timezone.utc)

        # Check if globally idle first
        if idle_seconds >= self.idle_threshold:
            return InteractionLevel.IDLE

        # Check for current keyboard activity
        if get_keyboard_activity():
            self.last_typing_time = now
            return InteractionLevel.TYPING

        # Check for current mouse activity
        if get_mouse_activity():
            self.last_click_time = now
            return InteractionLevel.CLICKING

        # Check if recent typing (within threshold)
        if self.last_typing_time:
            typing_age = (now - self.last_typing_time).total_seconds()
            if typing_age < self.interaction_threshold:
                return InteractionLevel.TYPING

        # Check if recent clicking (within threshold)
        if self.last_click_time:
            click_age = (now - self.last_click_time).total_seconds()
            if click_age < self.interaction_threshold:
                return InteractionLevel.CLICKING

        # No recent activity - passive reading/reference
        return InteractionLevel.PASSIVE
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_get_interaction_level_returns_idle_when_globally_idle tests/test_interaction_level.py::test_get_interaction_level_returns_passive_when_no_activity -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/tracker.py && git commit -m "feat: add get_interaction_level method to TrackerLoop"
```

---

### Task 5: Integrate Interaction Level into Tracking Loop (~4 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py:343-347` (state dict in start() method)
- **Modify:** `src/syncopaid/tracker.py:448-460` (_finalize_current_event method)
- **Modify:** `tests/test_interaction_level.py` (add integration test)

**Context:** Now we integrate get_interaction_level into the main tracking loop. The state dict needs to track interaction_level, and _finalize_current_event needs to include it in the ActivityEvent.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

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
    with patch('syncopaid.tracker.get_active_window', side_effect=mock_window):
        with patch('syncopaid.tracker.get_idle_seconds', side_effect=mock_idle):
            with patch('syncopaid.tracker.get_keyboard_activity', return_value=True):
                with patch('syncopaid.tracker.get_mouse_activity', return_value=False):
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
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_finalized_event_includes_interaction_level -v
```
Expected output: `FAILED` (interaction_level not tracked or not set to TYPING)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tracker.py (modify start() method state dict, around line 343-347)
# Change from:
                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'is_idle': is_idle
                }
# To:
                # Get interaction level
                interaction_level = self.get_interaction_level(idle_seconds)

                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'is_idle': is_idle,
                    'interaction_level': interaction_level.value
                }
```

```python
# src/syncopaid/tracker.py (modify _finalize_current_event method, around line 450-460)
# Change the ActivityEvent creation to include interaction_level:
        # Create event with start time, duration, end time, state, and interaction level
        event = ActivityEvent(
            timestamp=self.event_start_time.isoformat(),
            duration_seconds=round(duration, 2),
            app=self.current_event['app'],
            title=self.current_event['title'],
            end_time=end_time.isoformat(),
            url=None,  # URL extraction is future enhancement
            is_idle=self.current_event['is_idle'],
            state=event_state,
            interaction_level=self.current_event.get('interaction_level', InteractionLevel.PASSIVE.value)
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_finalized_event_includes_interaction_level -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/tracker.py && git commit -m "feat: integrate interaction level into tracking loop"
```

---

### Task 6: Add Database Schema Migration for interaction_level (~4 min)

**Files:**
- **Modify:** `src/syncopaid/database.py:67-142` (_init_schema method)
- **Modify:** `src/syncopaid/database.py:144-175` (insert_event method)
- **Modify:** `src/syncopaid/database.py:252-271` (get_events method)
- **Create:** `tests/test_interaction_level_db.py`

**Context:** The database needs to store interaction_level. We add a schema migration similar to the existing state column migration.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level_db.py
"""Tests for interaction level database storage."""

import pytest
import tempfile
import os
from syncopaid.database import Database
from syncopaid.tracker import ActivityEvent, InteractionLevel


def test_database_stores_interaction_level():
    """Verify database stores and retrieves interaction_level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        event = ActivityEvent(
            timestamp="2025-12-19T10:00:00",
            duration_seconds=300.0,
            app="WINWORD.EXE",
            title="Document.docx",
            interaction_level=InteractionLevel.TYPING.value
        )

        event_id = db.insert_event(event)
        assert event_id > 0

        events = db.get_events()
        assert len(events) == 1
        assert events[0]['interaction_level'] == "typing"


def test_database_migration_adds_interaction_level_column():
    """Verify schema migration adds interaction_level column."""
    import sqlite3

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")

        # Create database (runs migration)
        db = Database(db_path)

        # Check column exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert 'interaction_level' in columns
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level_db.py -v
```
Expected output: `FAILED` (interaction_level column doesn't exist)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (modify _init_schema, add after state column migration, around line 112)
            # Migration: Add interaction_level column if it doesn't exist
            if 'interaction_level' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN interaction_level TEXT DEFAULT 'passive'")
                logging.info("Database migration: Added interaction_level column to events table")
```

```python
# src/syncopaid/database.py (modify insert_event method, around line 154-175)
    def insert_event(self, event: ActivityEvent) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')
            interaction_level = getattr(event, 'interaction_level', 'passive')

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, interaction_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                1 if event.is_idle else 0,
                state,
                interaction_level
            ))

            return cursor.lastrowid
```

```python
# src/syncopaid/database.py (modify get_events method, around line 252-271)
# Update the event dictionary creation to include interaction_level:
                # Get interaction_level with fallback for older records
                if 'interaction_level' in row.keys() and row['interaction_level']:
                    interaction_level = row['interaction_level']
                else:
                    interaction_level = 'passive'

                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'duration_seconds': row['duration_seconds'],
                    'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                    'app': row['app'],
                    'title': row['title'],
                    'url': row['url'],
                    'is_idle': bool(row['is_idle']),
                    'state': state,
                    'interaction_level': interaction_level
                })
```

```python
# src/syncopaid/database.py (modify insert_events_batch method, around line 193-202)
            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state, interaction_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url, 1 if e.is_idle else 0,
                 getattr(e, 'state', 'Active'),
                 getattr(e, 'interaction_level', 'passive'))
                for e in events
            ])
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level_db.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level_db.py src/syncopaid/database.py && git commit -m "feat: add interaction_level column to database schema"
```

---

### Task 7: Add Config Setting for interaction_threshold (~3 min)

**Files:**
- **Modify:** `src/syncopaid/config.py:16-39` (DEFAULT_CONFIG)
- **Modify:** `src/syncopaid/config.py:42-90` (Config dataclass)
- **Modify:** `tests/test_interaction_level.py` (add config test)

**Context:** The interaction_threshold should be configurable so users can tune sensitivity. Following the existing config patterns.

**Step 1 - RED:** Write failing test
```python
# tests/test_interaction_level.py (append to file)

def test_config_has_interaction_threshold():
    """Verify config includes interaction_threshold_seconds setting."""
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'interaction_threshold_seconds' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['interaction_threshold_seconds'] == 5.0

    # Verify Config dataclass accepts it
    config = Config(interaction_threshold_seconds=10.0)
    assert config.interaction_threshold_seconds == 10.0
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_interaction_level.py::test_config_has_interaction_threshold -v
```
Expected output: `FAILED` (interaction_threshold_seconds not in config)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/config.py (add to DEFAULT_CONFIG dict, around line 38)
    # Interaction level detection
    "interaction_threshold_seconds": 5.0
```

```python
# src/syncopaid/config.py (add to Config dataclass, around line 89)
    # Interaction level detection
    interaction_threshold_seconds: float = 5.0
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_interaction_level.py::test_config_has_interaction_threshold -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_interaction_level.py src/syncopaid/config.py && git commit -m "feat: add interaction_threshold_seconds to config"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid.tracker            # Module runs without error (30s test)
python -m syncopaid.database           # Database module runs
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- **Privacy maintained**: Only tracks timing of activity, never keystroke content or mouse coordinates
- **GetAsyncKeyState polling**: Checks key state at poll time, not logging keystrokes
- **Interaction age**: Using threshold-based "recent activity" allows smooth transitions
- **Backward compatibility**: Database migration defaults existing records to 'passive'
- **Follow-up work**: Story 8.5 (LLM API Integration) can use interaction_level for better categorization hints
