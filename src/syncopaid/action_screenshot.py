"""
Action-based screenshot capture module.

Captures screenshots when user performs specific actions:
- Mouse clicks
- Enter/Return key presses
- Drag start operations
- Drag end (drop) operations
- Window focus changes (Alt+Tab, taskbar clicks, etc.)

Screenshots are saved to screenshots/actions/ with format:
YYYY-MM-DD_HH-mm-dd_UTC_{action}.jpg
"""

import sys
import logging
import time
from pathlib import Path

# Import worker class
from syncopaid.action_screenshot_worker import ActionScreenshotWorker

# Import utilities for testing
from syncopaid.action_screenshot_events import PYNPUT_AVAILABLE
from syncopaid.action_screenshot_capture import (
    get_action_screenshot_directory,
    WINDOWS_APIS_AVAILABLE
)

# Platform detection
WINDOWS = sys.platform == 'win32'

# Import PIL for type hints
try:
    from PIL import Image
except ImportError:
    class Image:
        class Image:
            pass

if WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError:
        pass


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Action Screenshot module test")
    print(f"Windows APIs available: {WINDOWS_APIS_AVAILABLE}")
    print(f"pynput available: {PYNPUT_AVAILABLE}")
    print(f"Default action screenshot directory: {get_action_screenshot_directory()}")

    if WINDOWS_APIS_AVAILABLE and PYNPUT_AVAILABLE:
        print("\nStarting action screenshot capture test...")
        print("Click your mouse, press Enter, or drag to test screenshot capture")
        print("Press Ctrl+C to stop\n")

        # Create test worker
        def mock_db_insert(**kwargs):
            print(f"DB Insert: captured_at={kwargs.get('captured_at', 'N/A')[:19]}, "
                  f"action={Path(kwargs.get('file_path', '')).stem.split('_')[-1]}")

        worker = ActionScreenshotWorker(
            screenshot_dir=get_action_screenshot_directory() / 'test',
            db_insert_callback=mock_db_insert,
            enabled=True
        )

        # Start listening
        worker.start()

        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping test...")
            worker.shutdown(wait=True)
            print(f"\n✓ Test complete")
            print(f"Stats: {worker.get_stats()}")
    else:
        print("\n⚠ Cannot test: Windows APIs or pynput not available")
