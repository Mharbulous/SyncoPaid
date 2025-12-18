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
