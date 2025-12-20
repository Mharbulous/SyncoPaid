# 030: UI Automation - TrackerLoop Integration

## Task
Integrate UIAutomationWorker into TrackerLoop to extract metadata during event finalization.

## Context
TrackerLoop captures window activity events. This integration calls the UI automation worker when finalizing events to populate the metadata field.

## Scope
- Add ui_automation_worker parameter to TrackerLoop.__init__()
- Store window_info in event state for extraction
- Call worker.extract() in _finalize_current_event()
- Populate ActivityEvent.metadata field

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tracker.py` | Add integration |
| `tests/test_tracker.py` | Test integration |

## Implementation

### Step 1: Add parameter to TrackerLoop

```python
# src/syncopaid/tracker.py - TrackerLoop.__init__()
def __init__(
    self,
    poll_interval: float = 0,
    idle_threshold: float = 180.0,
    merge_threshold: float = 2.0,
    screenshot_worker=None,
    screenshot_interval: float = 10.0,
    ui_automation_worker=None  # NEW
):
    # ...
    self.ui_automation_worker = ui_automation_worker
```

### Step 2: Store window_info in state

```python
# In start() while loop, after getting window info:
state = {
    'app': window['app'],
    'title': window['title'],
    'is_idle': is_idle,
    'window_info': window  # NEW - for UI automation
}
```

### Step 3: Extract metadata in _finalize_current_event()

```python
# src/syncopaid/tracker.py - in _finalize_current_event()
metadata = None
if self.ui_automation_worker and 'window_info' in self.current_event:
    metadata = self.ui_automation_worker.extract(self.current_event['window_info'])

event = ActivityEvent(
    # ... existing fields ...
    metadata=metadata,  # NEW
)
```

## Tests

```python
# tests/test_tracker.py (add)
def test_tracker_loop_ui_automation_integration():
    from syncopaid.tracker import TrackerLoop
    from syncopaid.ui_automation import UIAutomationWorker

    ui_worker = UIAutomationWorker(enabled=True)
    tracker = TrackerLoop(
        poll_interval=0,
        idle_threshold=180.0,
        merge_threshold=2.0,
        ui_automation_worker=ui_worker
    )

    assert tracker.ui_automation_worker is ui_worker
```

## Verification

```bash
venv\Scripts\activate
python -m pytest tests/test_tracker.py::test_tracker_loop_ui_automation_integration -v
python -m syncopaid.tracker  # Should run without errors
```

## Dependencies
- Task 028 (module creation)
- Task 029 (configuration)

## Next Task
After this: `031_ui-automation-outlook-extraction.md`
