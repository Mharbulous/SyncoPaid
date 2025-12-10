"""
Screenshot Diagnostic Tool for LawTime Tracker

Run this script to diagnose why screenshots aren't being captured.
"""

import sys
import os
import logging
from pathlib import Path

print("="*70)
print("LawTime Tracker - Screenshot Diagnostic Tool")
print("="*70)
print()

# Check 1: Platform
print("1. Platform Check")
print(f"   Platform: {sys.platform}")
is_windows = sys.platform == 'win32'
print(f"   Windows: {'✓ YES' if is_windows else '✗ NO (screenshots require Windows)'}")
print()

# Check 2: Dependencies
print("2. Dependency Check")
dependencies = {
    'win32gui': False,
    'win32process': False,
    'psutil': False,
    'PIL': False,
    'imagehash': False,
}

try:
    import win32gui
    dependencies['win32gui'] = True
    print("   ✓ win32gui (pywin32)")
except ImportError as e:
    print(f"   ✗ win32gui (pywin32) - {e}")

try:
    import win32process
    dependencies['win32process'] = True
    print("   ✓ win32process (pywin32)")
except ImportError as e:
    print(f"   ✗ win32process (pywin32) - {e}")

try:
    import psutil
    dependencies['psutil'] = True
    print("   ✓ psutil")
except ImportError as e:
    print(f"   ✗ psutil - {e}")

try:
    from PIL import Image, ImageGrab
    dependencies['PIL'] = True
    print("   ✓ PIL (Pillow) with ImageGrab")
except ImportError as e:
    print(f"   ✗ PIL (Pillow) - {e}")

try:
    import imagehash
    dependencies['imagehash'] = True
    print("   ✓ imagehash")
except ImportError as e:
    print(f"   ✗ imagehash - {e}")

print()

# Check 3: Configuration
print("3. Configuration Check")
try:
    from lawtime.config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.config

    print(f"   Config file: {config_manager.config_path}")
    print(f"   ✓ screenshot_enabled: {config.screenshot_enabled}")
    print(f"   ✓ screenshot_interval_seconds: {config.screenshot_interval_seconds}")
    print(f"   ✓ screenshot_quality: {config.screenshot_quality}")
    print(f"   ✓ screenshot_max_dimension: {config.screenshot_max_dimension}")
except Exception as e:
    print(f"   ✗ Error loading config: {e}")

print()

# Check 4: Screenshot directory
print("4. Screenshot Directory Check")
try:
    from lawtime.screenshot import get_screenshot_directory
    screenshot_dir = get_screenshot_directory()
    print(f"   Screenshot directory: {screenshot_dir}")
    print(f"   Exists: {'✓ YES' if screenshot_dir.exists() else '✗ NO'}")

    if screenshot_dir.exists():
        # Count existing screenshots
        jpg_files = list(screenshot_dir.rglob("*.jpg"))
        print(f"   Existing screenshots: {len(jpg_files)}")
        if jpg_files:
            print(f"   Most recent: {jpg_files[-1]}")
except Exception as e:
    print(f"   ✗ Error checking directory: {e}")

print()

# Check 5: Can we import screenshot module?
print("5. Screenshot Module Check")
try:
    from lawtime.screenshot import ScreenshotWorker, WINDOWS_APIS_AVAILABLE
    print(f"   ✓ screenshot.py imported successfully")
    print(f"   WINDOWS_APIS_AVAILABLE: {WINDOWS_APIS_AVAILABLE}")

    if not WINDOWS_APIS_AVAILABLE:
        print("   ⚠ WARNING: WINDOWS_APIS_AVAILABLE is False!")
        print("     This means screenshot.py couldn't import required modules.")
        print("     Check that PIL and imagehash are installed correctly.")
except Exception as e:
    print(f"   ✗ Error importing screenshot module: {e}")
    import traceback
    traceback.print_exc()

print()

# Check 6: Can we import tracker module?
print("6. Tracker Module Check")
try:
    from lawtime.tracker import TrackerLoop, WINDOWS_APIS_AVAILABLE as TRACKER_APIS
    print(f"   ✓ tracker.py imported successfully")
    print(f"   WINDOWS_APIS_AVAILABLE (tracker): {TRACKER_APIS}")

    if not TRACKER_APIS:
        print("   ⚠ WARNING: tracker's WINDOWS_APIS_AVAILABLE is False!")
        print("     This means tracker.py couldn't import win32gui/psutil.")
except Exception as e:
    print(f"   ✗ Error importing tracker module: {e}")
    import traceback
    traceback.print_exc()

print()

# Check 7: Database
print("7. Database Check")
try:
    from lawtime.database import Database
    config_manager = ConfigManager()
    db_path = config_manager.get_database_path()
    print(f"   Database path: {db_path}")
    print(f"   Exists: {'✓ YES' if db_path.exists() else '✗ NO'}")

    if db_path.exists():
        db = Database(str(db_path))
        screenshots = db.get_screenshots(limit=5)
        print(f"   Screenshot records in DB: {len(screenshots)}")
        if screenshots:
            print(f"   Most recent: {screenshots[0]['captured_at']}")
except Exception as e:
    print(f"   ✗ Error checking database: {e}")

print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)

all_deps_ok = all(dependencies.values())
if all_deps_ok and is_windows:
    print("✓ All dependencies installed correctly")
    print()
    print("Next steps:")
    print("1. Run the app: python -m lawtime")
    print("2. Wait at least 10 seconds")
    print("3. Check the console for these log messages:")
    print("   - 'Screenshot capture enabled: interval=10s'")
    print("   - 'Screenshot submitted #1 for [app name]'")
    print("   - 'Screenshot captured #1 (width x height)'")
    print("4. If you don't see these messages, check the log output")
else:
    print("✗ Issues detected:")
    if not is_windows:
        print("  - Not running on Windows (screenshots require Windows)")
    for dep, installed in dependencies.items():
        if not installed:
            print(f"  - Missing dependency: {dep}")

    print()
    print("To fix missing dependencies:")
    print("  pip install -r requirements.txt")

print("="*70)
