"""Tests for night processing scheduler."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from syncopaid.night_processor import NightProcessor


def test_is_night_window_during_night():
    processor = NightProcessor(start_hour=18, end_hour=8)
    with patch('syncopaid.night_processor.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 22, 0)  # 10 PM
        assert processor.is_night_window() is True


def test_is_night_window_during_day():
    processor = NightProcessor(start_hour=18, end_hour=8)
    with patch('syncopaid.night_processor.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 14, 0)  # 2 PM
        assert processor.is_night_window() is False


def test_is_night_window_early_morning():
    processor = NightProcessor(start_hour=18, end_hour=8)
    with patch('syncopaid.night_processor.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 6, 0)  # 6 AM
        assert processor.is_night_window() is True


def test_should_process_idle_and_night():
    processor = NightProcessor(
        start_hour=18, end_hour=8,
        idle_threshold_minutes=30,
        get_idle_seconds=lambda: 1900  # ~31 minutes
    )
    with patch('syncopaid.night_processor.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 22, 0)
        assert processor.should_process() is True


def test_should_process_not_idle_enough():
    processor = NightProcessor(
        start_hour=18, end_hour=8,
        idle_threshold_minutes=30,
        get_idle_seconds=lambda: 600  # 10 minutes
    )
    with patch('syncopaid.night_processor.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 22, 0)
        assert processor.should_process() is False


def test_should_process_disabled():
    processor = NightProcessor(enabled=False)
    assert processor.should_process() is False


def test_trigger_manual():
    mock_process = MagicMock(return_value=10)
    processor = NightProcessor(process_batch=mock_process)

    result = processor.trigger_manual()

    assert result == 10
    mock_process.assert_called_once_with(50)
