# Window Interaction Level Detection - Part A: Infrastructure

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add core infrastructure for interaction level detection - enum, detection functions, and tracker state.
**Approach:** Create InteractionLevel enum, add keyboard/mouse detection functions using GetAsyncKeyState, and add tracking state to TrackerLoop.
**Tech Stack:** pywin32 (`ctypes.windll.user32`), existing tracker.py infrastructure

---

**Story ID:** 1.1.3 | **Created:** 2025-12-19 | **Stage:** `planned`
**Sub-plan:** A of 3 (Infrastructure)

---

## Story Context

**Title:** Window Interaction Level Detection
**Description:** Current idle detection (tracker.py:174-197) uses GetLastInputInfo to detect global user activity, but doesn't distinguish between active typing in Word vs passive reading of a PDF. Lawyers need granular time attribution: 15 minutes reading a contract should be billable but categorized differently than 15 minutes drafting a motion.

**Acceptance Criteria (this sub-plan):**
- [ ] Add InteractionLevel enum (typing/clicking/passive/idle)
- [ ] Add interaction_level field to ActivityEvent
- [ ] Add keyboard/mouse activity detection functions
- [ ] Add interaction tracking state to TrackerLoop

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

## Final Verification (Sub-plan A)

Run after all tasks complete:
```bash
python -m pytest tests/test_interaction_level.py -v    # All sub-plan tests pass
python -m syncopaid.tracker                            # Module runs without error (30s test)
```

## Next Sub-plan

Continue with `013B_interaction-level-method-integration.md` which adds the get_interaction_level method and integrates it into the tracking loop.

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- **Privacy maintained**: Only tracks timing of activity, never keystroke content
- **GetAsyncKeyState polling**: Checks key state at poll time, not logging keystrokes
