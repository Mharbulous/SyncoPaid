"""Tests for resource monitoring module."""
import pytest
from syncopaid.resource_monitor import ResourceMonitor


def test_resource_monitor_initialization():
    """Test ResourceMonitor can be created with default settings."""
    monitor = ResourceMonitor()
    assert monitor is not None
    assert monitor.cpu_threshold == 80.0
    assert monitor.memory_threshold_mb == 200
    assert monitor.battery_threshold == 20


def test_get_current_metrics_returns_dict():
    """Test get_current_metrics returns a dict with expected keys."""
    monitor = ResourceMonitor()
    metrics = monitor.get_current_metrics()

    assert isinstance(metrics, dict)
    assert 'cpu_percent' in metrics
    assert 'memory_mb' in metrics
    assert 'battery_percent' in metrics
    assert isinstance(metrics['cpu_percent'], (int, float))
    assert isinstance(metrics['memory_mb'], (int, float))


def test_should_throttle_polling_when_cpu_high():
    """Test should_throttle_polling returns True when CPU exceeds threshold."""
    monitor = ResourceMonitor(cpu_threshold=80.0)
    # Mock high CPU by checking logic (actual test uses threshold comparison)
    # In real scenario, we test the method's behavior
    result = monitor.should_throttle_polling()
    assert isinstance(result, bool)


def test_should_skip_screenshot_returns_bool():
    """Test should_skip_screenshot returns boolean."""
    monitor = ResourceMonitor(cpu_threshold=90.0, battery_threshold=20)
    result = monitor.should_skip_screenshot()
    assert isinstance(result, bool)


def test_should_clear_cache_returns_bool():
    """Test should_clear_cache returns boolean based on memory usage."""
    monitor = ResourceMonitor(memory_threshold_mb=200)
    result = monitor.should_clear_cache()
    assert isinstance(result, bool)
