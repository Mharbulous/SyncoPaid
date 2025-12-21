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
from concurrent.futures import ThreadPoolExecutor

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
    ScreenshotMetadata,
    ComparisonResult,
    compute_dhash,
    compare_screenshots
)
from syncopaid.screenshot_persistence import (
    get_screenshot_directory,
    get_screenshot_path,
    save_screenshot
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
        idle_skip_seconds: int = 30
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
        self.screenshot_dir = screenshot_dir
        self.db_insert_callback = db_insert_callback
        self.threshold_identical = threshold_identical
        self.threshold_significant = threshold_significant
        self.threshold_identical_same_window = threshold_identical_same_window
        self.threshold_identical_different_window = threshold_identical_different_window
        self.quality = quality
        self.max_dimension = max_dimension
        self.idle_skip_seconds = idle_skip_seconds

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
        self.total_submitted += 1
        logging.info(f"Screenshot submitted #{self.total_submitted} for {window_app}")

        # Submit to thread pool
        self.executor.submit(
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
            if idle_seconds > self.idle_skip_seconds:
                logging.debug(f"Skipping screenshot: idle {idle_seconds:.0f}s")
                self.total_skipped += 1
                return

            # Skip certain apps (lock screen, etc.)
            if window_app in SKIP_APPS:
                logging.debug(f"Skipping screenshot: {window_app}")
                self.total_skipped += 1
                return

            # Capture the screenshot
            img = capture_window(hwnd)
            if img is None:
                logging.info(f"Screenshot capture failed for {window_app} (window issue)")
                self.total_skipped += 1
                return

            self.total_captured += 1
            logging.info(f"Screenshot captured #{self.total_captured} ({img.size[0]}x{img.size[1]})")

            # Resize if needed
            img = resize_if_needed(img, self.max_dimension)

            # Fast-path check: sample pixels before hashing
            if self.last_metadata and quick_pixel_check(img, self.last_metadata.file_path):
                # Very similar, overwrite directly
                self._overwrite_screenshot(img, timestamp)
                return

            # Compute perceptual hash
            current_hash = compute_dhash(img, hash_size=12)

            # Compare with previous screenshot
            time_since_save = time.time() - self.last_save_time
            result = compare_screenshots(
                current_hash=current_hash,
                previous_metadata=self.last_metadata,
                current_window_app=window_app,
                current_window_title=window_title,
                time_since_save=time_since_save,
                threshold_identical_same_window=self.threshold_identical_same_window,
                threshold_identical_different_window=self.threshold_identical_different_window,
                threshold_significant=self.threshold_significant
            )

            # Execute the appropriate action
            if result.action == ComparisonResult.OVERWRITE:
                self._overwrite_screenshot(img, timestamp, current_hash)
            else:
                self._save_new_screenshot(img, timestamp, window_app, window_title, current_hash)

        except Exception as e:
            logging.error(f"Error in screenshot capture: {e}")

    def _save_new_screenshot(
        self,
        img: Image.Image,
        timestamp: str,
        window_app: Optional[str],
        window_title: Optional[str],
        dhash: imagehash.ImageHash
    ):
        """
        Save a new screenshot and insert database record.

        Args:
            img: PIL Image to save
            timestamp: ISO timestamp
            window_app: Application name
            window_title: Window title
            dhash: Perceptual hash
        """
        file_path = get_screenshot_path(self.screenshot_dir, timestamp, window_app)

        # Save image as JPEG
        save_screenshot(img, file_path, self.quality)

        # Store metadata
        self.last_metadata = ScreenshotMetadata(
            file_path=str(file_path),
            dhash=str(dhash),
            captured_at=timestamp,
            window_app=window_app,
            window_title=window_title
        )
        self.last_save_time = time.time()

        # Insert into database
        self.db_insert_callback(
            captured_at=timestamp,
            file_path=str(file_path),
            window_app=window_app,
            window_title=window_title,
            dhash=str(dhash)
        )

        self.total_saved += 1
        logging.info(f"Saved new screenshot: {file_path}")

    def _overwrite_screenshot(
        self,
        img: Image.Image,
        timestamp: str,
        dhash: Optional[imagehash.ImageHash] = None
    ):
        """
        Overwrite the previous screenshot (near-identical content).

        Args:
            img: PIL Image to save
            timestamp: ISO timestamp
            dhash: Optional updated hash
        """
        if not self.last_metadata:
            logging.warning("No previous screenshot to overwrite")
            return

        # Overwrite existing file
        file_path = Path(self.last_metadata.file_path)
        save_screenshot(img, file_path, self.quality)

        # Update metadata if hash provided
        if dhash:
            self.last_metadata.dhash = str(dhash)
        self.last_metadata.captured_at = timestamp

        self.total_overwritten += 1
        logging.info(f"Overwritten screenshot: {file_path.name}")

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the screenshot worker.

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

    def get_stats(self) -> dict:
        """Get screenshot capture statistics."""
        return {
            'submitted': self.total_submitted,
            'captured': self.total_captured,
            'saved': self.total_saved,
            'overwritten': self.total_overwritten,
            'skipped': self.total_skipped
        }


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
