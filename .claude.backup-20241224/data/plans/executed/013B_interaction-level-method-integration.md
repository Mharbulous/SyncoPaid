# Window Interaction Level Detection - Part B: Method & Integration

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add get_interaction_level method and integrate it into the tracking loop.
**Approach:** Create method that classifies interaction based on keyboard/mouse activity timing, then integrate into TrackerLoop's event finalization.
**Tech Stack:** pywin32, existing tracker.py infrastructure

---

**Story ID:** 1.1.3 | **Created:** 2025-12-19 | **Stage:** `planned`
**Sub-plan:** B of 3 (Method & Integration)
**Depends on:** 013A_interaction-level-infrastructure.md

---

## Story Context

**Title:** Window Interaction Level Detection
**Description:** Current idle detection (tracker.py:174-197) uses GetLastInputInfo to detect global user activity, but doesn't distinguish between active typing in Word vs passive reading of a PDF. Lawyers need granular time attribution: 15 minutes reading a contract should be billable but categorized differently than 15 minutes drafting a motion.

**Acceptance Criteria (this sub-plan):**
- [ ] Add get_interaction_level method to TrackerLoop
- [ ] Calculate interaction age to classify activity type
- [ ] Integrate interaction level into tracking loop events

## Prerequisites

- [ ] Sub-plan A completed (InteractionLevel enum, detection functions, tracker state)
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

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

## Final Verification (Sub-plan B)

Run after all tasks complete:
```bash
python -m pytest tests/test_interaction_level.py -v    # All sub-plan tests pass
python -m syncopaid.tracker                            # Module runs without error (30s test)
```

## Next Sub-plan

Continue with `013C_interaction-level-database-config.md` which adds database schema migration and config settings.

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- **Interaction age**: Using threshold-based "recent activity" allows smooth transitions
- **Priority order**: IDLE > TYPING > CLICKING > PASSIVE ensures correct classification
