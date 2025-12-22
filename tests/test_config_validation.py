"""Tests for configuration validation."""

import pytest
from syncopaid.config import Config


def test_idle_threshold_valid_range_accepted():
    """Valid idle threshold values (10-600s) should be accepted as-is."""
    # Test minimum valid value
    config = Config.from_dict({'idle_threshold_seconds': 10})
    assert config.idle_threshold_seconds == 10

    # Test maximum valid value
    config = Config.from_dict({'idle_threshold_seconds': 600})
    assert config.idle_threshold_seconds == 600

    # Test middle value
    config = Config.from_dict({'idle_threshold_seconds': 180})
    assert config.idle_threshold_seconds == 180
