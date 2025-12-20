"""Tests for tracker module."""
import pytest
from syncopaid.tracker import TrackerLoop
from syncopaid.ui_automation import UIAutomationWorker


def test_tracker_loop_ui_automation_integration():
    """Test TrackerLoop integration with UIAutomationWorker."""
    ui_worker = UIAutomationWorker(enabled=True)
    tracker = TrackerLoop(
        poll_interval=0,
        idle_threshold=180.0,
        merge_threshold=2.0,
        ui_automation_worker=ui_worker
    )

    assert tracker.ui_automation_worker is ui_worker


def test_tracker_loop_without_ui_automation():
    """Test TrackerLoop can run without UI automation worker."""
    tracker = TrackerLoop(
        poll_interval=0,
        idle_threshold=180.0,
        merge_threshold=2.0
    )

    assert tracker.ui_automation_worker is None
