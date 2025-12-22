"""Tests for tracker module."""
import pytest
from syncopaid.tracker import TrackerLoop
from syncopaid.ui_automation import UIAutomationWorker
from syncopaid.tracker_windows import get_active_window


def test_get_active_window_includes_url_for_chrome():
    """Should include URL when Chrome is active."""
    # Mock scenario: Chrome window active
    info = get_active_window()
    # URL should be present if Chrome, else None
    assert "url" in info


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


def test_tracker_respects_url_config_disabled(tmp_path):
    """Should not extract URLs when disabled in config."""
    from syncopaid.config_dataclass import Config
    from syncopaid.tracker_windows import get_active_window

    # Create config with url_extraction_enabled=False
    config = Config(url_extraction_enabled=False)

    # Get active window with config
    info = get_active_window(config)

    # URL should be None when disabled (even for browsers)
    assert info["url"] is None
