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
