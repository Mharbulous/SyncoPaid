# 041: Command Line Tracking - TrackerLoop Integration

## Task
Update TrackerLoop to propagate cmdline from get_active_window() through to ActivityEvent.

## Context
The TrackerLoop needs to store cmdline in its internal state and include it when creating ActivityEvent objects.

## Scope
- Add cmdline to state dictionary in start()
- Add cmdline to ActivityEvent in _finalize_current_event()

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tracker.py` | Modify TrackerLoop |
| `tests/test_cmdline_tracking.py` | Add test |

## Implementation

### Update state dictionary

```python
# src/syncopaid/tracker.py - in start() while loop
# Find the state dict creation and add cmdline:
state = {
    'app': window['app'],
    'title': window['title'],
    'is_idle': is_idle,
    'cmdline': window.get('cmdline')  # ADD THIS LINE
}
```

### Update _finalize_current_event

```python
# src/syncopaid/tracker.py - in _finalize_current_event()
# Add cmdline when creating ActivityEvent:
event = ActivityEvent(
    timestamp=self.event_start_time.isoformat(),
    duration_seconds=round(duration, 2),
    app=self.current_event['app'],
    title=self.current_event['title'],
    end_time=end_time.isoformat(),
    url=None,
    cmdline=self.current_event.get('cmdline'),  # ADD THIS LINE
    is_idle=self.current_event['is_idle'],
    state=event_state
)
```

### Test

```python
# tests/test_cmdline_tracking.py (add)
def test_tracker_loop_includes_cmdline_in_event():
    from syncopaid.tracker import TrackerLoop, ActivityEvent

    tracker = TrackerLoop(poll_interval=0.01, idle_threshold=180.0)

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
                events = []
                for i, event in enumerate(gen):
                    if isinstance(event, ActivityEvent):
                        events.append(event)
                    if i >= 3:
                        tracker.stop()
                        break

    activity_events = [e for e in events if isinstance(e, ActivityEvent)]
    assert len(activity_events) > 0
    assert activity_events[0].cmdline == ['chrome.exe', '--profile-directory=Work']
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_cmdline_tracking.py::test_tracker_loop_includes_cmdline_in_event -v
```

## Dependencies
- Task 040 (get_active_window update)

## Next Task
After this: `042_cmdline-database-schema.md`
