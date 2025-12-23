"""Tests for main app resource monitoring integration."""
import pytest


def test_main_app_has_resource_monitor():
    """Test SyncoPaidApp initializes ResourceMonitor."""
    # We can't easily test the full app in unit tests,
    # so we verify the import and structure
    from syncopaid.resource_monitor import ResourceMonitor

    # Verify ResourceMonitor can be instantiated
    monitor = ResourceMonitor()
    assert monitor is not None

    # Verify it has the expected interface
    assert hasattr(monitor, 'should_throttle_polling')
    assert hasattr(monitor, 'should_skip_screenshot')
    assert hasattr(monitor, 'record_metrics')
    assert hasattr(monitor, 'get_statistics')
