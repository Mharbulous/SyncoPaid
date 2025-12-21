"""
Screenshot save and overwrite actions for ScreenshotWorker.

Handles saving new screenshots and overwriting existing ones.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from syncopaid.screenshot_comparison import ScreenshotMetadata
from syncopaid.screenshot_persistence import (
    get_screenshot_path,
    save_screenshot
)

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


def save_new_screenshot(
    state,
    img: Image.Image,
    timestamp: str,
    window_app: Optional[str],
    window_title: Optional[str],
    dhash: imagehash.ImageHash
):
    """
    Save a new screenshot and insert database record.

    Args:
        state: WorkerState instance
        img: PIL Image to save
        timestamp: ISO timestamp
        window_app: Application name
        window_title: Window title
        dhash: Perceptual hash
    """
    file_path = get_screenshot_path(state.screenshot_dir, timestamp, window_app)

    # Save image as JPEG
    save_screenshot(img, file_path, state.quality)

    # Store metadata
    state.last_metadata = ScreenshotMetadata(
        file_path=str(file_path),
        dhash=str(dhash),
        captured_at=timestamp,
        window_app=window_app,
        window_title=window_title
    )
    state.last_save_time = time.time()

    # Insert into database
    state.db_insert_callback(
        captured_at=timestamp,
        file_path=str(file_path),
        window_app=window_app,
        window_title=window_title,
        dhash=str(dhash)
    )

    state.total_saved += 1
    logging.info(f"Saved new screenshot: {file_path}")


def overwrite_screenshot(
    state,
    img: Image.Image,
    timestamp: str,
    dhash: Optional[imagehash.ImageHash] = None
):
    """
    Overwrite the previous screenshot (near-identical content).

    Args:
        state: WorkerState instance
        img: PIL Image to save
        timestamp: ISO timestamp
        dhash: Optional updated hash
    """
    if not state.last_metadata:
        logging.warning("No previous screenshot to overwrite")
        return

    # Overwrite existing file
    file_path = Path(state.last_metadata.file_path)
    save_screenshot(img, file_path, state.quality)

    # Update metadata if hash provided
    if dhash:
        state.last_metadata.dhash = str(dhash)
    state.last_metadata.captured_at = timestamp

    state.total_overwritten += 1
    logging.info(f"Overwritten screenshot: {file_path.name}")
