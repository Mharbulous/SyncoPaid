# Screenshot Feature Implementation Handover

## Task
Implement periodic screenshot capture with perceptual hashing deduplication for LawTime Tracker.

## Problem Solved
Window titles lack context (Outlook shows "Inbox" not email subject, New Outlook is opaque). Screenshots capture content-rich state. Naive "screenshot on window change" captures empty windows—periodic capture solves this.

## Agreed Architecture

### Threading Model
Screenshot capture runs in **separate worker thread** to avoid blocking 1-second polling loop. Main thread submits (hwnd, timestamp) to queue, worker handles capture/hash/save async.

```python
class ScreenshotWorker:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.last_hash = None
        self.last_path = None

    def submit(self, hwnd, timestamp):
        self.executor.submit(self._capture_and_compare, hwnd, timestamp)
```

### Algorithm: dHash (not pHash)
dHash is 2-3x faster, sufficient for same-window consecutive comparisons. Use `imagehash` library with hash_size=12 for 144-bit precision.

```python
import imagehash
hash1 = imagehash.dhash(img1, hash_size=12)
similarity = 1 - ((hash1 - hash2) / 144.0)
```

### Two-Tier Similarity Threshold
- `≥0.92`: Overwrite previous (near-identical)
- `0.70-0.92`: Save new if >60s since last save, else overwrite
- `<0.70`: Save new (significant change)

Guarantees at least one screenshot/minute for audit trail.

### Fast-Path Optimization
Before hashing, sample 5 pixels (corners + center). If all within tolerance, skip hash—overwrite directly. Eliminates ~80% of hash computations.

### Storage
- JPEG quality=65 (text-heavy screens tolerate well, 3-5x smaller)
- Cap resolution at 1920px max dimension
- Path: `%LOCALAPPDATA%\TimeLogger\screenshots/YYYY-MM-DD/HHMMSS_appname.jpg`

### Database Schema
Separate table (one screenshot can span multiple events):

```sql
CREATE TABLE screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    file_path TEXT NOT NULL,
    window_app TEXT,
    window_title TEXT,
    dhash TEXT
);
CREATE INDEX idx_screenshots_time ON screenshots(captured_at);
```

Link via time-range join, not FK.

## Key Files

**Modify:**
- `lawtime/tracker.py` — Add screenshot submission in `TrackerLoop.start()` loop (line ~200-230)
- `lawtime/database.py` — Add screenshots table schema and insert method
- `lawtime/config.py` — Add screenshot_interval, thresholds, quality settings

**New:**
- `lawtime/screenshot.py` — ScreenshotWorker class, capture logic, hashing

**Reference:**
- `ai_docs/Handovers/Screenshot_Feature_Design_Review.md` — Original design doc with full rationale

**Red Herrings (skip):**
- `lawtime/exporter.py` — JSON export, unrelated
- `lawtime/tray.py` — System tray UI, no changes needed for MVP
- `test_*.py` — Old API verification scripts, not unit tests
- `ai_docs/compass_artifact_*.md` — Commercial product comparisons

## Edge Cases to Handle

```python
def safe_capture_window(hwnd):
    if not win32gui.IsWindow(hwnd): return None
    if not win32gui.IsWindowVisible(hwnd): return None
    if win32gui.IsIconic(hwnd): return None  # Minimized

    rect = win32gui.GetWindowRect(hwnd)
    # Validate rect dimensions (width/height > 0, < 10000)
    # Clamp to screen bounds for partially off-screen windows
    # Skip if completely off-screen
```

Skip screenshots when:
- Idle >30 seconds (likely lock screen)
- App in `{'LockApp.exe', 'ScreenSaver.scr', 'LogonUI.exe'}`

## Dependencies
- `imagehash` — Add to requirements.txt (`pip install imagehash`)
- `Pillow` — Already installed (pystray dependency)
- `pywin32` — Already installed

## Config Defaults
```python
screenshot_interval_seconds = 10
screenshot_threshold_identical = 0.92
screenshot_threshold_significant = 0.70
screenshot_quality = 65
screenshot_max_dimension = 1920
screenshot_enabled = True
```

## Resources
- imagehash library: https://github.com/JohannesBuchner/imagehash
- pHash algorithm explanation: https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like.html
- Hash algorithm comparison: https://content-blockchain.org/research/testing-different-image-hash-functions/
- Pillow ImageGrab: https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html

## Environment
- Dev: WSL2 Ubuntu (cannot test Windows APIs)
- Target: Windows 11
- Python 3.11+
