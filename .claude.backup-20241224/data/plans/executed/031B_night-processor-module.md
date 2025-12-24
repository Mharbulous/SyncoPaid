# 031B: Night Processor Module
Story ID: 15.2

## Task
Create the NightProcessor class for scheduled overnight screenshot analysis.

## Context
This is the second sub-plan for Story 15.2 (Night Processing Mode). This creates the core NightProcessor module with time-window and idle detection logic.

## Scope
- Create `src/syncopaid/night_processor.py` module
- Create `tests/test_night_processor.py` with time-window tests

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/night_processor.py` | New module (CREATE) |
| `tests/test_night_processor.py` | Create test file (CREATE) |

## Implementation

### 1. Night Processor Module

```python
# src/syncopaid/night_processor.py (CREATE)
"""Overnight screenshot processing scheduler."""
import logging
import threading
import time
from datetime import datetime
from typing import Callable, Optional


class NightProcessor:
    """
    Schedules screenshot analysis during overnight idle periods.

    Monitors time-of-day and idle state to trigger batch processing
    when user is not actively working.
    """

    def __init__(
        self,
        start_hour: int = 18,
        end_hour: int = 8,
        idle_threshold_minutes: int = 30,
        batch_size: int = 50,
        get_idle_seconds: Callable[[], float] = None,
        get_pending_count: Callable[[], int] = None,
        process_batch: Callable[[int], int] = None,
        enabled: bool = True
    ):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.idle_threshold_seconds = idle_threshold_minutes * 60
        self.batch_size = batch_size
        self.enabled = enabled

        self._get_idle_seconds = get_idle_seconds
        self._get_pending_count = get_pending_count
        self._process_batch = process_batch

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._processing = False
        self._last_check = None

    def is_night_window(self) -> bool:
        """Check if current time is within night processing window."""
        hour = datetime.now().hour
        if self.start_hour > self.end_hour:
            # Crosses midnight (e.g., 18-8)
            return hour >= self.start_hour or hour < self.end_hour
        else:
            # Same day (e.g., 22-6)
            return self.start_hour <= hour < self.end_hour

    def should_process(self) -> bool:
        """Determine if conditions are met to start processing."""
        if not self.enabled:
            return False
        if not self.is_night_window():
            return False
        if self._get_idle_seconds is None:
            return False
        idle_seconds = self._get_idle_seconds()
        return idle_seconds >= self.idle_threshold_seconds

    def start(self):
        """Start the night processor monitor thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logging.info("Night processor started")

    def stop(self):
        """Stop the night processor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logging.info("Night processor stopped")

    def _monitor_loop(self):
        """Main monitoring loop - checks every 60 seconds."""
        while self._running:
            try:
                if self.should_process() and not self._processing:
                    self._run_processing()
            except Exception as e:
                logging.error(f"Night processor error: {e}")
            time.sleep(60)  # Check every minute

    def _run_processing(self):
        """Run a batch of screenshot processing."""
        if self._get_pending_count is None or self._process_batch is None:
            return

        pending = self._get_pending_count()
        if pending == 0:
            return

        self._processing = True
        logging.info(f"Night processing: {pending} screenshots pending")

        try:
            processed = self._process_batch(self.batch_size)
            logging.info(f"Night processing: processed {processed} screenshots")
        finally:
            self._processing = False

    def trigger_manual(self) -> int:
        """Manually trigger processing (for on-demand use)."""
        if self._process_batch is None:
            return 0
        return self._process_batch(self.batch_size)
```

### 2. Tests

```python
# tests/test_night_processor.py (CREATE)
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
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_night_processor.py -v
python -c "from syncopaid.night_processor import NightProcessor; print('OK')"
```

## Dependencies
- 031A: Night Processing Config (config settings must exist)

## Notes
- Callback-based design allows dependency injection for testing
- Threading model is daemon-based for clean shutdown
