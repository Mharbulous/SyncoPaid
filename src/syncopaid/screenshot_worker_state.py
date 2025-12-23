"""
State management and initialization for ScreenshotWorker.

Manages worker state, statistics, and initialization logic.
"""

import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from syncopaid.screenshot_comparison import ScreenshotMetadata


class WorkerState:
    """
    State container for ScreenshotWorker.

    Manages configuration, thread pool, metadata tracking, and statistics.
    """

    def __init__(
        self,
        screenshot_dir: Path,
        db_insert_callback,
        threshold_identical: float = 0.92,
        threshold_significant: float = 0.70,
        threshold_identical_same_window: float = 0.90,
        threshold_identical_different_window: float = 0.99,
        quality: int = 65,
        max_dimension: int = 1920,
        idle_skip_seconds: int = 30,
        resource_monitor=None
    ):
        """
        Initialize worker state.

        Args:
            screenshot_dir: Base directory for storing screenshots
            db_insert_callback: Function to call for inserting screenshot records
            threshold_identical: Similarity >= this overwrites previous (default: 0.92)
            threshold_significant: Similarity < this saves new screenshot (default: 0.70)
            threshold_identical_same_window: Threshold when window unchanged (default: 0.90)
            threshold_identical_different_window: Threshold when window changed (default: 0.99)
            quality: JPEG quality 1-100 (default: 65)
            max_dimension: Max width/height in pixels (default: 1920)
            idle_skip_seconds: Skip screenshots if idle > this many seconds (default: 30)
        """
        # Configuration
        self.screenshot_dir = screenshot_dir
        self.db_insert_callback = db_insert_callback
        self.threshold_identical = threshold_identical
        self.threshold_significant = threshold_significant
        self.threshold_identical_same_window = threshold_identical_same_window
        self.threshold_identical_different_window = threshold_identical_different_window
        self.quality = quality
        self.max_dimension = max_dimension
        self.idle_skip_seconds = idle_skip_seconds
        self.resource_monitor = resource_monitor

        # Thread pool for async capture
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='screenshot')

        # State tracking
        self.last_metadata: Optional[ScreenshotMetadata] = None
        self.last_save_time: float = 0

        # Statistics
        self.total_submitted = 0
        self.total_captured = 0
        self.total_saved = 0
        self.total_overwritten = 0
        self.total_skipped = 0

        # Ensure screenshot directory exists
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"ScreenshotWorker initialized: {screenshot_dir}")

    def get_stats(self) -> dict:
        """Get screenshot capture statistics."""
        return {
            'submitted': self.total_submitted,
            'captured': self.total_captured,
            'saved': self.total_saved,
            'overwritten': self.total_overwritten,
            'skipped': self.total_skipped
        }

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the worker thread pool.

        Args:
            wait: Whether to wait for pending tasks
            timeout: Max seconds to wait
        """
        logging.info(
            f"ScreenshotWorker shutting down. "
            f"Stats: submitted={self.total_submitted}, "
            f"captured={self.total_captured}, "
            f"saved={self.total_saved}, "
            f"overwritten={self.total_overwritten}, "
            f"skipped={self.total_skipped}"
        )
        self.executor.shutdown(wait=wait, cancel_futures=not wait)
