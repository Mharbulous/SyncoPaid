# 038: Command Line Tracking - ActivityEvent Field

## Task
Add `cmdline` field to the ActivityEvent dataclass.

## Context
First step for command line tracking. Adds the data structure to hold command line arguments, enabling distinction between multiple instances of the same application (e.g., Chrome profiles).

## Scope
- Add `cmdline: Optional[List[str]] = None` field to ActivityEvent
- Ensure to_dict() includes cmdline

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tracker.py` | Modify ActivityEvent dataclass |
| `tests/test_cmdline_tracking.py` | Create test file |

## Implementation

### Tests

```python
# tests/test_cmdline_tracking.py (CREATE)
"""Tests for process command line tracking functionality."""
import pytest
from syncopaid.tracker import ActivityEvent


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


if __name__ == "__main__":
    test_activity_event_has_cmdline_field()
    test_activity_event_cmdline_defaults_to_none()
    test_activity_event_to_dict_includes_cmdline()
    print("All tests passed!")
```

### Implementation

```python
# src/syncopaid/tracker.py - modify ActivityEvent dataclass
# Add after url field:
cmdline: Optional[List[str]] = None  # Process command line arguments
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_cmdline_tracking.py -v
```

## Dependencies
None - this is the first sub-plan for command line tracking.

## Next Task
After this: `039_cmdline-helper-functions.md`
