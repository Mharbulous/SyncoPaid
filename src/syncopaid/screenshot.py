"""
Screenshot capture module with perceptual hashing for deduplication.

Captures screenshots of active windows periodically with intelligent deduplication
using dHash (difference hash) algorithm. Runs in a separate thread to avoid blocking
the main tracking loop.
"""

import sys
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import decomposed modules
from syncopaid.screenshot_capture import (
    capture_window,
    resize_if_needed,
    quick_pixel_check,
    WINDOWS_APIS_AVAILABLE,
    SKIP_APPS,
    PIL_AVAILABLE
)
from syncopaid.screenshot_comparison import (
    ComparisonResult,
    compute_dhash,
    compare_screenshots
)
from syncopaid.screenshot_persistence import get_screenshot_directory
from syncopaid.screenshot_worker_state import WorkerState
from syncopaid.screenshot_worker_actions import (
    save_new_screenshot,
    overwrite_screenshot
)

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL and imagehash for type hints
try:
    from PIL import Image
    import imagehash
except ImportError:
    # Create dummy types for non-PIL environments
    class Image:
        class Image:
            pass
    class imagehash:
        class ImageHash:
            pass


class ScreenshotWorker:
    """
    Worker class for asynchronous screenshot capture and processing.

    Uses ThreadPoolExecutor to capture screenshots in background without
    blocking the main tracking loop. Implements perceptual hashing (dHash)
    for intelligent deduplication.
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
        Initialize the screenshot worker.

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
        self._state = WorkerState(
            screenshot_dir=screenshot_dir,
            db_insert_callback=db_insert_callback,
            threshold_identical=threshold_identical,
            threshold_significant=threshold_significant,
            threshold_identical_same_window=threshold_identical_same_window,
            threshold_identical_different_window=threshold_identical_different_window,
            quality=quality,
            max_dimension=max_dimension,
            idle_skip_seconds=idle_skip_seconds,
            resource_monitor=resource_monitor
        )

    def submit(
        self,
        hwnd: int,
        timestamp: str,
        window_app: Optional[str],
        window_title: Optional[str],
        idle_seconds: float
    ):
        """
        Submit a screenshot capture request (non-blocking).

        Args:
            hwnd: Windows window handle
            timestamp: ISO timestamp when screenshot was requested
            window_app: Application name
            window_title: Window title
            idle_seconds: Current idle time in seconds
        """
        self._state.total_submitted += 1
        logging.info(f"Screenshot submitted #{self._state.total_submitted} for {window_app}")

        # Submit to thread pool
        self._state.executor.submit(
            self._capture_and_compare,
            hwnd,
            timestamp,
            window_app,
            window_title,
            idle_seconds
        )

    def _capture_and_compare(
        self,
        hwnd: int,
        timestamp: str,
        window_app: Optional[str],
        window_title: Optional[str],
        idle_seconds: float
    ):
        """
        Capture screenshot and compare with previous (runs in worker thread).

        Args:
            hwnd: Windows window handle
            timestamp: ISO timestamp
            window_app: Application name
            window_title: Window title
            idle_seconds: Current idle time
        """
        try:
            # Skip if idle too long
            if idle_seconds > self._state.idle_skip_seconds:
                logging.debug(f"Skipping screenshot: idle {idle_seconds:.0f}s")
                self._state.total_skipped += 1
                return

            # Skip if resources are constrained
            if self._state.resource_monitor and self._state.resource_monitor.should_skip_screenshot():
                logging.debug("Skipping screenshot: resource constraints")
                self._state.total_skipped += 1
                return

            # Skip certain apps (lock screen, etc.)
            if window_app in SKIP_APPS:
                logging.debug(f"Skipping screenshot: {window_app}")
                self._state.total_skipped += 1
                return

            # Capture the screenshot
            img = capture_window(hwnd)
            if img is None:
                logging.info(f"Screenshot capture failed for {window_app} (window issue)")
                self._state.total_skipped += 1
                return

            self._state.total_captured += 1
            logging.info(f"Screenshot captured #{self._state.total_captured} ({img.size[0]}x{img.size[1]})")

            # Resize if needed
            img = resize_if_needed(img, self._state.max_dimension)

            # Fast-path check: sample pixels before hashing
            if self._state.last_metadata and quick_pixel_check(img, self._state.last_metadata.file_path):
                # Very similar, overwrite directly
                overwrite_screenshot(self._state, img, timestamp)
                return

            # Compute perceptual hash
            current_hash = compute_dhash(img, hash_size=12)

            # Compare with previous screenshot
            time_since_save = time.time() - self._state.last_save_time
            result = compare_screenshots(
                current_hash=current_hash,
                previous_metadata=self._state.last_metadata,
                current_window_app=window_app,
                current_window_title=window_title,
                time_since_save=time_since_save,
                threshold_identical_same_window=self._state.threshold_identical_same_window,
                threshold_identical_different_window=self._state.threshold_identical_different_window,
                threshold_significant=self._state.threshold_significant
            )

            # Execute the appropriate action
            if result.action == ComparisonResult.OVERWRITE:
                overwrite_screenshot(self._state, img, timestamp, current_hash)
            else:
                save_new_screenshot(self._state, img, timestamp, window_app, window_title, current_hash)

        except Exception as e:
            logging.error(f"Error in screenshot capture: {e}")

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the screenshot worker.

        Args:
            wait: Whether to wait for pending tasks
            timeout: Max seconds to wait
        """
        self._state.shutdown(wait, timeout)

    def get_stats(self) -> dict:
        """Get screenshot capture statistics."""
        return self._state.get_stats()


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Screenshot module test")
    print(f"Windows APIs available: {WINDOWS_APIS_AVAILABLE}")
    print(f"Default screenshot directory: {get_screenshot_directory()}")

    if WINDOWS_APIS_AVAILABLE:
        import win32gui

        print("\nAttempting to capture current window...")

        # Get current foreground window
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        print(f"Window: {title}")

        # Create test worker
        def mock_db_insert(**kwargs):
            print(f"DB Insert: {kwargs}")

        worker = ScreenshotWorker(
            screenshot_dir=get_screenshot_directory() / 'test',
            db_insert_callback=mock_db_insert
        )

        # Submit screenshot
        timestamp = datetime.now(timezone.utc).isoformat()
        worker.submit(hwnd, timestamp, "test.exe", title, 0.0)

        # Wait for completion
        worker.shutdown(wait=True)

        print("\n✓ Screenshot test complete")
        print(f"Stats: {worker.get_stats()}")
    else:
        print("\n⚠ Cannot test on non-Windows platform")
