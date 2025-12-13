"""
Direct Screenshot Capture Test

This script bypasses the tracker and directly tests screenshot capture.
Run this on Windows to verify the screenshot functionality works.
"""

import sys
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

# Configure logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*70)
print("Direct Screenshot Capture Test")
print("="*70)
print()

# Check if on Windows
if sys.platform != 'win32':
    print("✗ ERROR: This test must be run on Windows")
    sys.exit(1)

print("✓ Running on Windows")
print()

# Try to import required modules
print("Importing modules...")
try:
    import win32gui
    print("  ✓ win32gui")
except ImportError as e:
    print(f"  ✗ win32gui failed: {e}")
    print("  Install: pip install pywin32")
    sys.exit(1)

try:
    from PIL import Image, ImageGrab
    print("  ✓ PIL with ImageGrab")
except ImportError as e:
    print(f"  ✗ PIL failed: {e}")
    print("  Install: pip install Pillow")
    sys.exit(1)

try:
    import imagehash
    print("  ✓ imagehash")
except ImportError as e:
    print(f"  ✗ imagehash failed: {e}")
    print("  Install: pip install imagehash")
    sys.exit(1)

print()

# Import screenshot module
print("Importing screenshot module...")
try:
    from SyncoPaid.screenshot import ScreenshotWorker, get_screenshot_directory, WINDOWS_APIS_AVAILABLE
    print(f"  ✓ screenshot module imported")
    print(f"  WINDOWS_APIS_AVAILABLE = {WINDOWS_APIS_AVAILABLE}")

    if not WINDOWS_APIS_AVAILABLE:
        print("  ✗ ERROR: WINDOWS_APIS_AVAILABLE is False!")
        print("  This means the screenshot module detected missing dependencies.")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Setup screenshot directory
screenshot_dir = get_screenshot_directory() / "test"
screenshot_dir.mkdir(parents=True, exist_ok=True)
print(f"Screenshot directory: {screenshot_dir}")
print()

# Create a mock database insert callback
screenshot_records = []
def mock_db_insert(**kwargs):
    screenshot_records.append(kwargs)
    print(f"  [DB] Screenshot record: {kwargs['file_path']}")

# Create screenshot worker
print("Creating ScreenshotWorker...")
worker = ScreenshotWorker(
    screenshot_dir=screenshot_dir,
    db_insert_callback=mock_db_insert,
    threshold_identical=0.92,
    threshold_significant=0.70,
    quality=65,
    max_dimension=1920,
    idle_skip_seconds=30
)
print("  ✓ Worker created")
print()

# Get current foreground window
print("Getting foreground window...")
try:
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    print(f"  Window handle: {hwnd}")
    print(f"  Window title: {title}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

print()

# Attempt screenshot capture
print("Attempting screenshot capture...")
print("(This will capture the current foreground window)")
print()

timestamp = datetime.now(timezone.utc).isoformat()

# Submit screenshot request
worker.submit(
    hwnd=hwnd,
    timestamp=timestamp,
    window_app="test.exe",
    window_title=title,
    idle_seconds=0.0
)

print("Screenshot request submitted to worker thread...")
print("Waiting for worker to complete (5 seconds)...")
time.sleep(5)

# Shutdown worker and wait for completion
print()
print("Shutting down worker...")
worker.shutdown(wait=True, timeout=10.0)

# Check results
print()
print("="*70)
print("RESULTS")
print("="*70)
stats = worker.get_stats()
print(f"Submitted: {stats['submitted']}")
print(f"Captured: {stats['captured']}")
print(f"Saved: {stats['saved']}")
print(f"Overwritten: {stats['overwritten']}")
print(f"Skipped: {stats['skipped']}")
print()

if stats['saved'] > 0:
    print("✓ SUCCESS! Screenshot was captured and saved.")
    print()
    print(f"Screenshot records: {len(screenshot_records)}")
    if screenshot_records:
        print(f"Last screenshot: {screenshot_records[-1]['file_path']}")
    print()
    print("Check the screenshot directory:")
    print(f"  {screenshot_dir}")

    # List files
    jpg_files = list(screenshot_dir.rglob("*.jpg"))
    if jpg_files:
        print()
        print("Files found:")
        for f in jpg_files:
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.1f} KB)")
elif stats['skipped'] > 0:
    print("⚠ Screenshot was skipped")
    print("  This might be because:")
    print("  - Window is minimized")
    print("  - Window is not visible")
    print("  - Window dimensions are invalid")
    print("  - System is idle (though we set idle_seconds=0)")
elif stats['captured'] > 0 and stats['saved'] == 0:
    print("⚠ Screenshot was captured but not saved")
    print("  This might indicate an issue with file writing or hashing")
else:
    print("✗ FAILED - No screenshot was captured")
    print("  Check the log output above for errors")

print()
print("If this test succeeds, the screenshot functionality works.")
print("The issue may be with the tracker integration or configuration.")
print("="*70)
