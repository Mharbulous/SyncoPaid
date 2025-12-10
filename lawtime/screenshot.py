"""
Screenshot capture module with perceptual hashing for deduplication.

Captures screenshots of active windows periodically with intelligent deduplication
using dHash (difference hash) algorithm. Runs in a separate thread to avoid blocking
the main tracking loop.
"""

import os
import sys
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL and imagehash regardless of platform (needed for type hints)
try:
    from PIL import Image
    import imagehash
    PIL_AVAILABLE = True
except ImportError as e:
    PIL_AVAILABLE = False
    logging.warning(f"PIL/imagehash import failed: {e}. Screenshots will be disabled.")
    # Create dummy types for non-PIL environments
    class Image:
        class Image:
            pass
    class imagehash:
        class ImageHash:
            pass

if WINDOWS:
    try:
        import win32gui
        from PIL import ImageGrab
        WINDOWS_APIS_AVAILABLE = PIL_AVAILABLE and True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Screenshot APIs not available. Install pywin32, Pillow, and imagehash.")
else:
    WINDOWS_APIS_AVAILABLE = False


# Apps to skip screenshot capture
SKIP_APPS = {
    'LockApp.exe',
    'ScreenSaver.scr',
    'LogonUI.exe'
}


@dataclass
class ScreenshotMetadata:
    """Metadata about a captured screenshot."""
    file_path: str
    dhash: str
    captured_at: str
    window_app: Optional[str]
    window_title: Optional[str]


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
            img = self._capture_window(hwnd)
            if img is None:
                logging.info(f"Screenshot capture failed for {window_app} (window issue)")
                self.total_skipped += 1
                return

            self.total_captured += 1
            logging.info(f"Screenshot captured #{self.total_captured} ({img.size[0]}x{img.size[1]})")

            # Resize if needed
            img = self._resize_if_needed(img)

            # Fast-path check: sample pixels before hashing
            if self.last_metadata and self._quick_pixel_check(img, self.last_metadata.file_path):
                # Very similar, overwrite directly
                self._overwrite_screenshot(img, timestamp)
                return

            # Compute perceptual hash
            current_hash = imagehash.dhash(img, hash_size=12)

            # Compare with previous screenshot
            if self.last_metadata:
                previous_hash = imagehash.hex_to_hash(self.last_metadata.dhash)
                hash_diff = current_hash - previous_hash
                similarity = 1 - (hash_diff / 144.0)  # 12x12 = 144 bits

                # Detect if active window has changed
                window_changed = window_app != self.last_metadata.window_app

                # Select appropriate threshold based on window context
                if window_changed:
                    # Window changed: use stricter threshold (99%)
                    # Only overwrite if nearly identical, handling edge cases where:
                    # - User returns to same window (duplicate screenshot)
                    # - User switches between identical content (same page in different tabs)
                    threshold = self.threshold_identical_different_window
                    logging.info(
                        f"Window changed: {self.last_metadata.window_app} -> {window_app}. "
                        f"Using strict threshold: {threshold}"
                    )
                else:
                    # Same window: use more permissive threshold (90%)
                    # Allow natural visual changes within same window
                    threshold = self.threshold_identical_same_window

                # Determine action based on similarity and threshold
                if similarity >= threshold:
                    # Meets threshold, overwrite
                    self._overwrite_screenshot(img, timestamp, current_hash)
                    return

                elif similarity >= self.threshold_significant:
                    # Moderate similarity - check time since last save
                    time_since_save = time.time() - self.last_save_time
                    if time_since_save < 60:
                        # Less than 60s since last save, overwrite
                        self._overwrite_screenshot(img, timestamp, current_hash)
                        return

            # Save as new screenshot (either significantly different or 60s elapsed)
            self._save_new_screenshot(img, timestamp, window_app, window_title, current_hash)

        except Exception as e:
            logging.error(f"Error in screenshot capture: {e}")

    def _capture_window(self, hwnd: int) -> Optional[Image.Image]:
        """
        Capture screenshot of the specified window.

        Args:
            hwnd: Windows window handle

        Returns:
            PIL Image or None if capture failed
        """
        if not WINDOWS_APIS_AVAILABLE:
            # Mock screenshot for testing on non-Windows
            logging.debug("Mock screenshot (non-Windows platform)")
            return None

        try:
            # Validate window
            if not win32gui.IsWindow(hwnd):
                logging.debug("Invalid window handle")
                return None

            if not win32gui.IsWindowVisible(hwnd):
                logging.debug("Window not visible")
                return None

            if win32gui.IsIconic(hwnd):
                logging.debug("Window is minimized")
                return None

            # Get window rectangle
            rect = win32gui.GetWindowRect(hwnd)
            x1, y1, x2, y2 = rect
            width = x2 - x1
            height = y2 - y1

            # Validate dimensions
            if width <= 0 or height <= 0:
                logging.debug(f"Invalid window dimensions: {width}x{height}")
                return None

            if width > 10000 or height > 10000:
                logging.warning(f"Window too large: {width}x{height}")
                return None

            # Check if completely off-screen
            if x2 < 0 or y2 < 0:
                logging.debug("Window completely off-screen")
                return None

            # Capture the screenshot
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            return img

        except Exception as e:
            logging.error(f"Error capturing window: {e}")
            return None

    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Resize image if either dimension exceeds max_dimension.

        Args:
            img: PIL Image

        Returns:
            Resized PIL Image (or original if no resize needed)
        """
        width, height = img.size
        max_dim = max(width, height)

        if max_dim <= self.max_dimension:
            return img

        # Calculate new dimensions maintaining aspect ratio
        scale = self.max_dimension / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _quick_pixel_check(self, img: Image.Image, previous_path: str) -> bool:
        """
        Fast-path optimization: sample 5 pixels (corners + center).

        If all pixels are within tolerance, skip expensive hash computation.

        Args:
            img: Current image
            previous_path: Path to previous screenshot

        Returns:
            True if images appear identical via pixel sampling
        """
        try:
            if not os.path.exists(previous_path):
                return False

            prev_img = Image.open(previous_path)

            # Must be same size
            if img.size != prev_img.size:
                return False

            width, height = img.size

            # Sample 5 points: 4 corners + center
            sample_points = [
                (0, 0),
                (width - 1, 0),
                (0, height - 1),
                (width - 1, height - 1),
                (width // 2, height // 2)
            ]

            tolerance = 10  # RGB difference tolerance

            for x, y in sample_points:
                pixel1 = img.getpixel((x, y))
                pixel2 = prev_img.getpixel((x, y))

                # Convert to tuples if needed
                if isinstance(pixel1, int):
                    pixel1 = (pixel1, pixel1, pixel1)
                if isinstance(pixel2, int):
                    pixel2 = (pixel2, pixel2, pixel2)

                # Check RGB differences
                for i in range(min(3, len(pixel1))):
                    if abs(pixel1[i] - pixel2[i]) > tolerance:
                        return False

            # All sampled pixels are within tolerance
            return True

        except Exception as e:
            logging.debug(f"Quick pixel check failed: {e}")
            return False

    def _get_screenshot_path(self, timestamp: str, window_app: Optional[str]) -> Path:
        """
        Generate file path for screenshot.

        Format: {screenshot_dir}/YYYY-MM-DD/YYYY-MM-DD_HH-MM-SS_TZ_appname.jpg
        (e.g., 2025-12-09/2025-12-09_23-25-05_PST_WindowsTerminal.jpg)

        Args:
            timestamp: ISO timestamp with timezone information
            window_app: Application name

        Returns:
            Path object for screenshot file
        """
        dt = datetime.fromisoformat(timestamp)

        # Create date-based subdirectory (local date)
        date_dir = self.screenshot_dir / dt.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with date, time, and timezone abbreviation
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H-%M-%S')
        tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", "EST", etc.
        app_name = window_app if window_app else 'unknown'
        # Sanitize app name for filename
        app_name = app_name.replace('.exe', '').replace('.', '_')[:20]

        filename = f"{date_str}_{time_str}_{tz_abbr}_{app_name}.jpg"
        return date_dir / filename

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
        file_path = self._get_screenshot_path(timestamp, window_app)

        # Save image as JPEG
        img.save(str(file_path), 'JPEG', quality=self.quality, optimize=True)

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
        file_path = self.last_metadata.file_path
        img.save(file_path, 'JPEG', quality=self.quality, optimize=True)

        # Update metadata if hash provided
        if dhash:
            self.last_metadata.dhash = str(dhash)
        self.last_metadata.captured_at = timestamp

        self.total_overwritten += 1
        logging.info(f"Overwritten screenshot: {Path(file_path).name}")

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
# UTILITY FUNCTIONS
# ============================================================================

def get_screenshot_directory() -> Path:
    """
    Get the default screenshot storage directory.

    Returns:
        Path to screenshot directory
    """
    import sys
    import os

    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        screenshot_dir = appdata / 'TimeLogger' / 'screenshots'
    else:
        screenshot_dir = Path.home() / '.local' / 'share' / 'timelogger' / 'screenshots'

    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


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
