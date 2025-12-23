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
