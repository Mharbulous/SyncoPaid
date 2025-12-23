"""Tests for screenshot resource throttling."""
import pytest


def test_screenshot_worker_accepts_resource_monitor():
    """Test ScreenshotWorker can accept resource_monitor parameter."""
    from syncopaid.resource_monitor import ResourceMonitor
    from syncopaid.screenshot_worker_state import WorkerState
    from pathlib import Path
    import tempfile

    monitor = ResourceMonitor()

    with tempfile.TemporaryDirectory() as tmpdir:
        state = WorkerState(
            screenshot_dir=Path(tmpdir),
            db_insert_callback=lambda **kwargs: None,
            resource_monitor=monitor
        )

        assert state.resource_monitor is monitor
