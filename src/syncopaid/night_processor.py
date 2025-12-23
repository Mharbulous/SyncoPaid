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
