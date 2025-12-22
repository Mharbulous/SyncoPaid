"""Tests for configuration validation."""

import pytest
import logging
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


def test_idle_threshold_below_minimum_falls_back_to_default(caplog):
    """Idle threshold below 10s should fallback to default with warning."""
    with caplog.at_level(logging.WARNING):
        config = Config.from_dict({'idle_threshold_seconds': 5})

    # Should fallback to default (180s)
    assert config.idle_threshold_seconds == 180.0

    # Should log warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)


def test_idle_threshold_above_maximum_falls_back_to_default(caplog):
    """Idle threshold above 600s should fallback to default with warning."""
    with caplog.at_level(logging.WARNING):
        config = Config.from_dict({'idle_threshold_seconds': 700})

    # Should fallback to default (180s)
    assert config.idle_threshold_seconds == 180.0

    # Should log warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)
