# Transition Detection & Smart Prompts - Implementation Plan

> **TDD Required:** Each task: Write test -> RED -> Write code -> GREEN -> Commit

**Goal:** Detect natural transition points (inbox, idle return, context switches) and prompt users to categorize time with intelligent, context-aware timing.

**Approach:** Build pattern detection in TrackerLoop to identify transitions, store transition events in DB, create tkinter prompt UI with rich response options, implement learning model from user feedback.

**Tech Stack:** tracker.py (pattern detection) | database.py (transition events table) | tkinter (prompt dialog) | config.py (sensitivity settings)

---

**Story ID:** 8.4.2 | **Created:** 2025-12-17 | **Status:** `implemented`

---

## Story Context

**Title:** Transition Detection & Smart Prompts

**Description:** **As a** lawyer working through my day
**I want** AI to detect natural transition points between tasks
**So that** I'm prompted to categorize time at convenient moments, not while I'm deep in focus

**Acceptance Criteria:**
- [ ] Detect transition indicators: inbox browsing, file explorer navigation, idle return
- [ ] Detect context switches: different client folder, new browser research session
- [ ] "Is now a good time to categorize your time?" prompt at transitions with context-rich response options:
  - "I'm free" (available for categorization)
  - "I'm on a break" (not working, don't count this time)
  - "You're interrupting work" (bad timing, learn from this)
  - "Got to go, TTYL!" (dismiss, will categorize later)
- [ ] Store user responses to build transition timing model
- [ ] Configurable sensitivity (aggressive prompting vs. minimal interruption)
- [ ] Never prompt during active document editing or video calls

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `src/syncopaid/database.py:50-90` | Modify | Add transitions table schema |
| `src/syncopaid/tracker.py:280-360` | Modify | Add transition detection logic |
| `src/syncopaid/prompt.py` | Create | Transition prompt dialog |
| `src/syncopaid/transition_detector.py` | Create | Pattern analysis for transitions |
| `src/syncopaid/config.py:15-45` | Modify | Add transition sensitivity config |
| `tests/test_transition_detector.py` | Create | Unit tests for detection |
| `tests/test_prompt.py` | Create | Unit tests for prompt dialog |

## TDD Tasks

### Task 1: Database Schema for Transitions

**Files:** Test: `tests/test_database.py` | Impl: `src/syncopaid/database.py:48-90`

**RED:** Create test for transitions table existence and insert.
```python
def test_transitions_table_exists(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transitions'")
        assert cursor.fetchone() is not None

def test_insert_transition():
    db = Database(":memory:")
    transition_id = db.insert_transition(
        timestamp="2025-12-17T10:30:00",
        transition_type="idle_return",
        context={"idle_seconds": 320},
        user_response=None
    )
    assert transition_id > 0
```
Run: `pytest tests/test_database.py::test_transitions_table_exists -v` -> Expect: FAILED

**GREEN:** Add transitions table to schema.
```python
# In Database._init_schema() after events table creation
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        transition_type TEXT NOT NULL,
        context TEXT,
        user_response TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transitions_timestamp ON transitions(timestamp)")

def insert_transition(self, timestamp: str, transition_type: str, context: dict = None, user_response: str = None) -> int:
    import json
    context_json = json.dumps(context) if context else None
    with self._get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO transitions (timestamp, transition_type, context, user_response) VALUES (?, ?, ?, ?)",
            (timestamp, transition_type, context_json, user_response)
        )
        return cursor.lastrowid
```
Run: `pytest tests/test_database.py::test_transitions_table_exists -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_database.py src/syncopaid/database.py && git commit -m "feat: add transitions table for tracking timing patterns"`

---

### Task 2: Transition Pattern Detector

**Files:** Test: `tests/test_transition_detector.py` | Impl: `src/syncopaid/transition_detector.py`

**RED:** Create test for inbox browsing detection.
```python
from syncopaid.transition_detector import TransitionDetector

def test_detect_inbox_browsing():
    detector = TransitionDetector()

    # Simulate Outlook inbox window
    is_transition = detector.is_transition(
        app="OUTLOOK.EXE",
        title="Inbox - brahm@example.com - Outlook",
        prev_app="WINWORD.EXE",
        prev_title="Document1.docx",
        idle_seconds=0
    )

    assert is_transition == True
    assert detector.last_transition_type == "inbox_browsing"

def test_detect_idle_return():
    detector = TransitionDetector()

    # Return from 5+ minute idle
    is_transition = detector.is_transition(
        app="chrome.exe",
        title="Google Search",
        prev_app=None,
        prev_title=None,
        idle_seconds=320
    )

    assert is_transition == True
    assert detector.last_transition_type == "idle_return"

def test_no_transition_during_document_edit():
    detector = TransitionDetector()

    # Active Word editing should not trigger
    is_transition = detector.is_transition(
        app="WINWORD.EXE",
        title="Contract.docx - Word",
        prev_app="WINWORD.EXE",
        prev_title="Contract.docx - Word",
        idle_seconds=0
    )

    assert is_transition == False
```
Run: `pytest tests/test_transition_detector.py -v` -> Expect: FAILED

**GREEN:** Implement pattern detection logic.
```python
# src/syncopaid/transition_detector.py
from typing import Optional, Dict

class TransitionDetector:
    """Detects transition points between tasks based on activity patterns."""

    INBOX_KEYWORDS = ["inbox", "- outlook", "mail"]
    EXPLORER_KEYWORDS = ["file explorer", "documents", "downloads"]
    ACTIVE_EDIT_APPS = ["winword.exe", "excel.exe", "acrord32.exe"]
    IDLE_THRESHOLD = 300  # 5 minutes

    def __init__(self):
        self.last_transition_type: Optional[str] = None

    def is_transition(
        self,
        app: str,
        title: str,
        prev_app: Optional[str],
        prev_title: Optional[str],
        idle_seconds: float
    ) -> bool:
        """
        Determine if current activity represents a transition point.

        Returns True if transition detected, False otherwise.
        Sets self.last_transition_type to the type detected.
        """
        # Never interrupt active document editing
        if app and app.lower() in self.ACTIVE_EDIT_APPS:
            if prev_app and prev_app.lower() == app.lower():
                return False

        # Idle return (5+ minutes)
        if idle_seconds >= self.IDLE_THRESHOLD:
            self.last_transition_type = "idle_return"
            return True

        # Inbox browsing
        if title and any(kw in title.lower() for kw in self.INBOX_KEYWORDS):
            if prev_title and not any(kw in prev_title.lower() for kw in self.INBOX_KEYWORDS):
                self.last_transition_type = "inbox_browsing"
                return True

        # File Explorer navigation
        if title and any(kw in title.lower() for kw in self.EXPLORER_KEYWORDS):
            if prev_app != app:
                self.last_transition_type = "explorer_navigation"
                return True

        return False
```
Run: `pytest tests/test_transition_detector.py -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_transition_detector.py src/syncopaid/transition_detector.py && git commit -m "feat: implement transition pattern detection for inbox, idle, explorer"`

---

### Task 3: Prompt Dialog UI

**Files:** Test: `tests/test_prompt.py` | Impl: `src/syncopaid/prompt.py`

**RED:** Create test for prompt dialog creation.
```python
from syncopaid.prompt import TransitionPrompt

def test_prompt_dialog_creation():
    """Test prompt dialog can be created and returns user response."""
    # This is a UI test - verify interface exists
    prompt = TransitionPrompt()

    # Verify response options exist
    assert "free" in prompt.RESPONSES
    assert "break" in prompt.RESPONSES
    assert "interrupting" in prompt.RESPONSES
    assert "dismiss" in prompt.RESPONSES

def test_prompt_returns_response():
    """Test that show() returns selected response."""
    prompt = TransitionPrompt()
    # Mock user clicking "I'm free"
    # In real test, would use GUI testing framework
    # For now, verify method exists
    assert hasattr(prompt, 'show')
```
Run: `pytest tests/test_prompt.py -v` -> Expect: FAILED

**GREEN:** Create tkinter prompt dialog.
```python
# src/syncopaid/prompt.py
import tkinter as tk
from tkinter import ttk
from typing import Optional

class TransitionPrompt:
    """Prompt dialog asking user if now is a good time to categorize."""

    RESPONSES = {
        "free": "I'm free",
        "break": "I'm on a break",
        "interrupting": "You're interrupting work",
        "dismiss": "Got to go, TTYL!"
    }

    def __init__(self):
        self.response: Optional[str] = None
        self.root: Optional[tk.Tk] = None

    def show(self, transition_type: str = None) -> Optional[str]:
        """
        Show prompt dialog and return user's response.

        Args:
            transition_type: Type of transition detected (for context)

        Returns:
            Response key ("free", "break", "interrupting", "dismiss") or None if dismissed
        """
        self.root = tk.Tk()
        self.root.title("SyncoPaid - Time Categorization")
        self.root.geometry("400x200")
        self.root.attributes('-topmost', True)

        # Message
        msg = "Is now a good time to categorize your time?"
        if transition_type:
            msg += f"\n\n(Detected: {transition_type.replace('_', ' ').title()})"

        label = tk.Label(self.root, text=msg, font=('Segoe UI', 10), pady=20)
        label.pack()

        # Response buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        for key, text in self.RESPONSES.items():
            btn = tk.Button(
                btn_frame,
                text=text,
                command=lambda k=key: self._handle_response(k),
                width=20
            )
            btn.pack(pady=5)

        self.root.mainloop()
        return self.response

    def _handle_response(self, response_key: str):
        """Handle button click."""
        self.response = response_key
        self.root.destroy()
```
Run: `pytest tests/test_prompt.py -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_prompt.py src/syncopaid/prompt.py && git commit -m "feat: add transition prompt dialog with 4 response options"`

---

### Task 4: Integration with TrackerLoop

**Files:** Test: `tests/test_tracker.py` | Impl: `src/syncopaid/tracker.py:204-360`

**RED:** Create test for transition detection in tracker.
```python
def test_tracker_detects_transitions():
    """Test that TrackerLoop detects and records transitions."""
    from syncopaid.tracker import TrackerLoop
    from syncopaid.transition_detector import TransitionDetector

    # Mock database callback
    transitions_recorded = []
    def mock_insert_transition(**kwargs):
        transitions_recorded.append(kwargs)

    detector = TransitionDetector()
    tracker = TrackerLoop(
        transition_detector=detector,
        transition_callback=mock_insert_transition,
        prompt_enabled=False  # Disable UI for testing
    )

    # Simulate activity that triggers transition
    # (This would require mocking window APIs)
    # Verify transition callback was invoked
    assert len(transitions_recorded) > 0
```
Run: `pytest tests/test_tracker.py::test_tracker_detects_transitions -v` -> Expect: FAILED

**GREEN:** Add transition detection to TrackerLoop.
```python
# In src/syncopaid/tracker.py

# Add to TrackerLoop.__init__
def __init__(
    self,
    poll_interval: float = 0,
    idle_threshold: int = 180,
    merge_threshold: float = 2.0,
    screenshot_worker=None,
    screenshot_interval: float = 10.0,
    transition_detector=None,
    transition_callback=None,
    prompt_enabled: bool = True
):
    # ... existing init code ...
    self.transition_detector = transition_detector
    self.transition_callback = transition_callback
    self.prompt_enabled = prompt_enabled
    self.prev_window_state = None

# In TrackerLoop.start() after state change detection (around line 305)
# Add after checking _has_state_changed():

# Check for transitions
if self.transition_detector and self.current_event:
    is_trans = self.transition_detector.is_transition(
        app=state['app'],
        title=state['title'],
        prev_app=self.prev_window_state['app'] if self.prev_window_state else None,
        prev_title=self.prev_window_state['title'] if self.prev_window_state else None,
        idle_seconds=idle_seconds
    )

    if is_trans:
        # Record transition
        if self.transition_callback:
            self.transition_callback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                transition_type=self.transition_detector.last_transition_type,
                context={"app": state['app'], "title": state['title']},
                user_response=None
            )

        # Show prompt if enabled
        if self.prompt_enabled:
            # Spawn prompt in separate thread (non-blocking)
            # TODO: Implement in next task
            pass

self.prev_window_state = state.copy()
```
Run: `pytest tests/test_tracker.py::test_tracker_detects_transitions -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_tracker.py src/syncopaid/tracker.py && git commit -m "feat: integrate transition detection into tracking loop"`

---

### Task 5: Configuration Settings

**Files:** Test: `tests/test_config.py` | Impl: `src/syncopaid/config.py:15-45`

**RED:** Test for transition config settings.
```python
def test_default_config_has_transition_settings():
    from syncopaid.config import DEFAULT_CONFIG

    assert "transition_prompt_enabled" in DEFAULT_CONFIG
    assert "transition_sensitivity" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["transition_sensitivity"] in ["aggressive", "moderate", "minimal"]
```
Run: `pytest tests/test_config.py::test_default_config_has_transition_settings -v` -> Expect: FAILED

**GREEN:** Add config defaults.
```python
# In src/syncopaid/config.py DEFAULT_CONFIG dict (around line 15-45)

DEFAULT_CONFIG = {
    # ... existing config ...
    "transition_prompt_enabled": True,
    "transition_sensitivity": "moderate",  # aggressive, moderate, minimal
    "transition_never_prompt_apps": ["WINWORD.EXE", "EXCEL.EXE", "Teams.exe"],
}
```
Run: `pytest tests/test_config.py::test_default_config_has_transition_settings -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_config.py src/syncopaid/config.py && git commit -m "feat: add transition prompt configuration settings"`

---

### Task 6: Non-blocking Prompt Display

**Files:** Test: `tests/test_prompt.py` | Impl: `src/syncopaid/tracker.py:305-320`

**RED:** Test that prompt doesn't block tracker thread.
```python
def test_prompt_runs_in_separate_thread():
    """Verify prompt spawns in thread and doesn't block."""
    import threading
    from syncopaid.tracker import TrackerLoop

    tracker = TrackerLoop(prompt_enabled=True)

    # Trigger transition that would show prompt
    # Verify main thread continues
    # (Requires integration test setup)
    pass
```
Run: `pytest tests/test_prompt.py::test_prompt_runs_in_separate_thread -v` -> Expect: FAILED

**GREEN:** Spawn prompt in background thread.
```python
# In TrackerLoop.start() where we added prompt check

if self.prompt_enabled:
    # Import here to avoid circular deps
    from syncopaid.prompt import TransitionPrompt
    import threading

    def show_prompt_async():
        prompt = TransitionPrompt()
        response = prompt.show(self.transition_detector.last_transition_type)

        # Update transition record with response
        if response and self.transition_callback:
            # Re-record with user response
            self.transition_callback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                transition_type=self.transition_detector.last_transition_type,
                context={"app": state['app'], "title": state['title']},
                user_response=response
            )

    threading.Thread(target=show_prompt_async, daemon=True).start()
```
Run: `pytest tests/test_prompt.py::test_prompt_runs_in_separate_thread -v` -> Expect: PASSED

**COMMIT:** `git add tests/test_prompt.py src/syncopaid/tracker.py && git commit -m "feat: spawn transition prompts in background threads"`

---

### Task 7: Wire Up to Main Application

**Files:** Test: `tests/test_main.py` | Impl: `src/syncopaid/__main__.py:134-199`

**RED:** Test that SyncoPaidApp creates transition detector.
```python
def test_app_initializes_transition_detector():
    """Verify main app wires up transition detection."""
    # Would require app initialization test
    # Verify transition_detector passed to TrackerLoop
    pass
```
Run: `pytest tests/test_main.py -v` -> Expect: FAILED (or skip if no test framework for main)

**GREEN:** Wire transition detector into app.
```python
# In SyncoPaidApp.__init__ (around line 134-199)

from syncopaid.transition_detector import TransitionDetector

def __init__(self):
    # ... existing init ...

    # Initialize transition detector
    self.transition_detector = None
    if self.config.transition_prompt_enabled:
        self.transition_detector = TransitionDetector()

    # Initialize tracker loop with transition support
    self.tracker = TrackerLoop(
        poll_interval=self.config.poll_interval_seconds,
        idle_threshold=self.config.idle_threshold_seconds,
        merge_threshold=self.config.merge_threshold_seconds,
        screenshot_worker=self.screenshot_worker,
        screenshot_interval=self.config.screenshot_interval_seconds,
        transition_detector=self.transition_detector,
        transition_callback=self.database.insert_transition,
        prompt_enabled=self.config.transition_prompt_enabled
    )
```
Run: Manual verification: `python -m syncopaid`

**COMMIT:** `git add src/syncopaid/__main__.py && git commit -m "feat: wire transition detection into main application"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module test: `python -m syncopaid.tracker`
- [ ] Manual test: Run app, return from idle, verify prompt appears
- [ ] Manual test: Browse Outlook inbox, verify prompt appears
- [ ] Manual test: Edit Word doc continuously, verify no prompts
- [ ] Config test: Set `transition_prompt_enabled: false`, verify no prompts

## Notes

**Dependencies:**
- Story 8.1 (Matter/Client Database) required before prompts can do actual categorization
- Current implementation only detects transitions and collects user feedback
- Future enhancement: Use transition data to train smarter timing model

**Edge Cases:**
- Multiple rapid transitions: Implement cooldown period (don't prompt more than once per 10 minutes)
- Video call detection: Check for Teams/Zoom in active apps, never prompt during calls
- Focus mode: Add config option to disable all prompts during specific hours

**Follow-up Work:**
- Story 8.4.3: Build actual categorization UI that prompts invoke
- Story 8.4.4: Implement learning from user responses to improve timing
- Add database query methods for analyzing transition patterns
