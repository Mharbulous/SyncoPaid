"""
Screenshot comparison and deduplication logic.

Implements perceptual hashing (dHash) and similarity comparison to determine
whether screenshots should be saved as new files or overwrite existing ones.
"""

import logging
from typing import Optional
from dataclasses import dataclass

try:
    from PIL import Image
    import imagehash
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Create dummy types
    class Image:
        class Image:
            pass
    class imagehash:
        class ImageHash:
            pass


@dataclass
class ScreenshotMetadata:
    """Metadata about a captured screenshot."""
    file_path: str
    dhash: str
    captured_at: str
    window_app: Optional[str]
    window_title: Optional[str]


class ComparisonResult:
    """Result of comparing current screenshot with previous."""

    SAVE_NEW = "save_new"
    OVERWRITE = "overwrite"

    def __init__(self, action: str, similarity: Optional[float] = None):
        self.action = action
        self.similarity = similarity


def compute_dhash(img: Image.Image, hash_size: int = 12) -> 'imagehash.ImageHash':
    """
    Compute perceptual hash (dHash) for an image.

    Args:
        img: PIL Image
        hash_size: Hash size (default: 12, produces 144-bit hash)

    Returns:
        ImageHash object
    """
    return imagehash.dhash(img, hash_size=hash_size)


def compare_screenshots(
    current_hash: 'imagehash.ImageHash',
    previous_metadata: Optional[ScreenshotMetadata],
    current_window_app: Optional[str],
    current_window_title: Optional[str],
    time_since_save: float,
    threshold_identical_same_window: float = 0.90,
    threshold_identical_different_window: float = 0.99,
    threshold_significant: float = 0.70
) -> ComparisonResult:
    """
    Compare current screenshot with previous to determine save strategy.

    Args:
        current_hash: Hash of current screenshot
        previous_metadata: Metadata from previous screenshot
        current_window_app: Current window application name
        current_window_title: Current window title
        time_since_save: Seconds since last save
        threshold_identical_same_window: Threshold when window unchanged (default: 0.90)
        threshold_identical_different_window: Threshold when window changed (default: 0.99)
        threshold_significant: Similarity < this saves new screenshot (default: 0.70)

    Returns:
        ComparisonResult indicating whether to save new or overwrite
    """
    # No previous screenshot - always save new
    if not previous_metadata:
        return ComparisonResult(ComparisonResult.SAVE_NEW)

    # Compare hashes
    previous_hash = imagehash.hex_to_hash(previous_metadata.dhash)
    hash_diff = current_hash - previous_hash
    similarity = 1 - (hash_diff / 144.0)  # 12x12 = 144 bits

    # Detect if active window has changed (either app or title)
    window_changed = (
        current_window_app != previous_metadata.window_app or
        current_window_title != previous_metadata.window_title
    )

    # Select appropriate threshold based on window context
    if window_changed:
        # Window changed: use stricter threshold (99%)
        # Only overwrite if nearly identical, handling edge cases where:
        # - User returns to same window (duplicate screenshot)
        # - User switches between identical content (same page in different tabs)
        threshold = threshold_identical_different_window

        # Log the change details
        if current_window_app != previous_metadata.window_app:
            logging.info(
                f"App changed: {previous_metadata.window_app} -> {current_window_app}. "
                f"Using strict threshold: {threshold}"
            )
        else:
            logging.info(
                f"Window title changed (same app: {current_window_app}). "
                f"Using strict threshold: {threshold}"
            )
    else:
        # Same window: use more permissive threshold (90%)
        # Allow natural visual changes within same window
        threshold = threshold_identical_same_window

    # Determine action based on similarity and threshold
    if similarity >= threshold:
        # Meets threshold, overwrite
        return ComparisonResult(ComparisonResult.OVERWRITE, similarity)

    elif similarity >= threshold_significant:
        # Moderate similarity - check time since last save
        if time_since_save < 60:
            # Less than 60s since last save, overwrite
            return ComparisonResult(ComparisonResult.OVERWRITE, similarity)

    # Save as new screenshot (either significantly different or 60s elapsed)
    return ComparisonResult(ComparisonResult.SAVE_NEW, similarity)
