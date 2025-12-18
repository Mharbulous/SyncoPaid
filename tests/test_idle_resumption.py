"""Tests for idle resumption detection functionality."""

import pytest
from datetime import datetime, timezone
from syncopaid.tracker import IdleResumptionEvent


def test_idle_resumption_event_creation():
    """Verify IdleResumptionEvent can be instantiated with required fields."""
    resumption_time = datetime(2025, 12, 18, 10, 30, 0, tzinfo=timezone.utc)
    event = IdleResumptionEvent(
        resumption_timestamp=resumption_time.isoformat(),
        idle_duration=900.0  # 15 minutes
    )

    assert event.resumption_timestamp == "2025-12-18T10:30:00+00:00"
    assert event.idle_duration == 900.0


def test_idle_resumption_event_to_dict():
    """Verify IdleResumptionEvent can be converted to dictionary."""
    resumption_time = datetime(2025, 12, 18, 10, 30, 0, tzinfo=timezone.utc)
    event = IdleResumptionEvent(
        resumption_timestamp=resumption_time.isoformat(),
        idle_duration=900.0
    )

    data = event.to_dict()
    assert data['resumption_timestamp'] == "2025-12-18T10:30:00+00:00"
    assert data['idle_duration'] == 900.0


def test_config_has_minimum_idle_duration():
    """Verify config includes minimum_idle_duration setting."""
    from syncopaid.config import DEFAULT_CONFIG, Config

    assert 'minimum_idle_duration_seconds' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['minimum_idle_duration_seconds'] == 180

    # Verify Config dataclass accepts it
    config = Config(minimum_idle_duration_seconds=300)
    assert config.minimum_idle_duration_seconds == 300


def test_tracker_loop_init_idle_resumption_state():
    """Verify TrackerLoop initializes idle resumption tracking state."""
    from syncopaid.tracker import TrackerLoop

    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        minimum_idle_duration=180.0
    )

    assert hasattr(tracker, 'was_idle')
    assert tracker.was_idle is False
    assert hasattr(tracker, 'last_idle_resumption_time')
    assert tracker.last_idle_resumption_time is None
    assert hasattr(tracker, 'minimum_idle_duration')
    assert tracker.minimum_idle_duration == 180.0


def test_detect_idle_to_active_transition():
    """Verify idle→active transition emits IdleResumptionEvent."""
    from syncopaid.tracker import TrackerLoop, IdleResumptionEvent
    from unittest.mock import patch
    from datetime import datetime, timezone

    tracker = TrackerLoop(
        poll_interval=0.01,
        idle_threshold=5.0,
        minimum_idle_duration=3.0
    )

    # Simulate changing windows to trigger state changes
    # iteration 1: idle at TestApp, iteration 2: active at DifferentApp, iteration 3: active at DifferentApp
    windows = [
        {'app': 'TestApp.exe', 'title': 'Test1', 'pid': 1234},
        {'app': 'DifferentApp.exe', 'title': 'Test2', 'pid': 5678},  # Changed app to force state change
        {'app': 'DifferentApp.exe', 'title': 'Test2', 'pid': 5678}
    ]
    idle_values = [10.0, 0.0, 0.0]  # idle → active → active

    call_count = [0]

    def mock_window():
        idx = min(call_count[0], len(windows) - 1)
        return windows[idx]

    def mock_idle():
        idx = call_count[0]
        call_count[0] += 1
        return idle_values[min(idx, len(idle_values) - 1)]

    events = []
    with patch('syncopaid.tracker.get_active_window', side_effect=mock_window):
        with patch('syncopaid.tracker.get_idle_seconds', side_effect=mock_idle):
            with patch('time.sleep'):  # Mock sleep to speed up test
                gen = tracker.start()
                # Collect first few events
                for _ in range(5):
                    try:
                        event = next(gen)
                        events.append(event)
                    except StopIteration:
                        break
                tracker.stop()

    # Should have emitted IdleResumptionEvent
    resumption_events = [e for e in events if isinstance(e, IdleResumptionEvent)]
    assert len(resumption_events) == 1, f"Expected 1 resumption event, got {len(resumption_events)}"
    assert resumption_events[0].idle_duration == 10.0
