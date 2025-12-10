# Screenshot Capture Feature - Design Review Handover

## Current State
**Planning phase.** No code written yet. Evaluating technical approach for adding screenshot capture to address context limitations.

## Task
Review and critically evaluate the proposed screenshot capture solution. Refine for optimal performance, robustness, and storage efficiency.

## Problem Statement

### Context Gap in Current Implementation
LawTime tracks window titles and app names, but many applications lack sufficient context:
- **Outlook:** Reading pane shows generic "Inbox" instead of specific email subjects
- **New Outlook:** Completely opaque to subject extraction
- **Browser tabs:** URL capture not implemented (title only)
- **Document editors:** Title may not reflect current section being edited

### User Insight (Critical)
"Taking a screenshot on every window change captures when the window is **first opened**, not when it's being **closed**. The problem is that when a window is ready to be closed, it is most **content-rich**."

This ruled out naive "screenshot-on-window-change" approach.

## Proposed Solution

### Architecture: Periodic Capture + Perceptual Hashing

```python
# Pseudocode
SCREENSHOT_INTERVAL = 10  # seconds
last_screenshot = None
last_hash = None

while tracking:
    if time_for_screenshot():
        new_screenshot = capture_active_window()
        new_hash = compute_perceptual_hash(new_screenshot)

        similarity = compare_hashes(new_hash, last_hash)

        if similarity > 0.80:
            # Content unchanged - overwrite previous
            overwrite_file(last_screenshot_path, new_screenshot)
        else:
            # Significant change - save new file
            save_new_screenshot(new_screenshot)
```

### Key Design Decisions

1. **Capture active window only** (not full screen)
   - Smaller file size
   - Privacy: only what user is working on
   - Easier to match with activity events

2. **Periodic capture** (not event-based)
   - Captures content-rich state during use
   - Multiple snapshots for long-duration activities
   - Avoids technical issues with non-foreground windows

3. **Smart overwriting via perceptual hashing**
   - Compare each screenshot to previous
   - If >80% similar: overwrite (saves storage)
   - If <80% similar: save new file (captures change)
   - Detects content changes even without window change (e.g., scrolling in Outlook reading pane)

## Technical Implementation Details

### Image Capture (Easy - Already Have Dependencies)
**Pillow is already installed** (dependency of pystray for system tray).

```python
from PIL import ImageGrab
import win32gui

# Get active window bounding box
hwnd = win32gui.GetForegroundWindow()
bbox = win32gui.GetWindowRect(hwnd)

# Capture just that window
screenshot = ImageGrab.grab(bbox)
screenshot.save(f"screenshot_{timestamp}.jpg", quality=85)
```

File size: ~1-5 MB per JPEG (quality=85), vs ~3-10 MB for PNG.

### Perceptual Hashing Algorithms Evaluated

#### Option 1: Perceptual Hash (pHash) - RECOMMENDED
**Library:** `imagehash` (https://github.com/JohannesBuchner/imagehash)

```python
import imagehash

hash1 = imagehash.phash(img1)  # 64-bit hash
hash2 = imagehash.phash(img2)
difference = hash1 - hash2  # Hamming distance (0-64)
similarity = 1 - (difference / 64.0)
```

- **Performance:** ~5-10ms per comparison
- **Robust:** Handles minor UI shifts, window position changes
- **Battle-tested:** Used in duplicate photo finders
- **Add dependency:** `pip install imagehash`

**Algorithm:** DCT-based (Discrete Cosine Transform), similar to JPEG compression. Converts image to frequency domain, takes low-frequency components. Invariant to minor visual changes.

Resources:
- https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html (pHash explanation)
- https://pypi.org/project/ImageHash/

#### Option 2: Difference Hash (dHash) - DIY
No external dependencies.

```python
def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size))
    pixels = np.array(image)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()
```

- **Performance:** ~3-5ms
- **Simpler:** Horizontal gradient-based
- **Less robust:** More sensitive to shifts

#### Option 3: MSE (Mean Squared Error) - FASTEST
```python
img1_small = np.array(img1.resize((200, 150)))
img2_small = np.array(img2.resize((200, 150)))
mse = np.mean((img1_small - img2_small) ** 2)
similarity = 1 - (mse / (255 ** 2))
```

- **Performance:** ~1-2ms
- **Problem:** Highly sensitive to pixel shifts (scrollbar position, cursor, etc.)
- **Not recommended** for this use case

### Storage Estimates

**Scenario 1:** Reading email for 5 minutes
- Without hashing: 30 screenshots @ 3MB = 90 MB
- With hashing (80% threshold): 1-2 screenshots = 3-6 MB
- **Savings: 93-97%**

**Scenario 2:** Actively editing document
- Without hashing: 30 screenshots = 90 MB
- With hashing: 10-15 screenshots (typing changes detected) = 30-45 MB
- **Savings: 50-67%**

## Integration Points

### Relevant Files

**Must modify:**
- `lawtime/tracker.py:187-243` - `TrackerLoop.start()` generator loop
  - Add screenshot capture logic every N seconds
  - Track last_screenshot_hash for comparison
  - Handle screenshot file paths

- `lawtime/database.py:67-102` - Schema modification
  - Add `screenshot_path TEXT` column to events table
  - Link screenshots to time ranges
  - Consider screenshot cleanup on event deletion

- `lawtime/config.py` - Add configuration
  - `screenshot_interval_seconds: 10`
  - `screenshot_similarity_threshold: 0.80`
  - `screenshot_quality: 85` (JPEG)

**Storage location:**
```
%LOCALAPPDATA%\TimeLogger\
├── lawtime.db
├── config.json
└── screenshots/
    ├── 2025-12-10/
    │   ├── screenshot_20251210_143052.jpg
    │   └── screenshot_20251210_143102.jpg
    └── 2025-12-11/
        └── ...
```

### Red Herrings (Skip These)
- `lawtime/exporter.py` - JSON export (unrelated to screenshot capture)
- `test_*.py` - Old API verification scripts
- `ai_docs/compass_artifact_*.md` - Commercial comparisons
- `lawtime/tray.py` - System tray UI (no changes needed for MVP)

## Technical Questions for Review

### 1. Algorithm Choice
Is **pHash the right choice**, or would dHash be sufficient given:
- Minimal dependency footprint preferred
- 5-10ms latency acceptable (polling is every 1 second)
- Need to detect scrolling, email changes, document edits
- Should tolerate minor UI shifts (scrollbar, cursor)

### 2. Similarity Threshold
Is **80% the optimal threshold**?
- Too high (90%+): May save too many near-duplicates (wasted storage)
- Too low (60-70%): May miss legitimate content (overwrite important changes)
- Should threshold vary by application type?

### 3. Database Schema
**Option A:** Store screenshot_path in events table
```sql
events: id, timestamp, duration_seconds, app, title, screenshot_path
```
Problem: One screenshot may span multiple events if user stays in same window.

**Option B:** Separate screenshots table
```sql
screenshots: id, timestamp, file_path, window_app, window_title
events: id, timestamp, duration_seconds, app, title
```
Link via timestamp range queries.

Which is cleaner?

### 4. Orphan File Cleanup
If events are deleted (user exports and purges old data), screenshots may become orphaned. Solutions:
- Reference counting in DB
- Periodic cleanup job (delete screenshots not referenced by events)
- Ignore (user manually cleans screenshot folder)

### 5. Performance Impact
- Will capturing 1-5 MB screenshots every 10s impact tracking accuracy?
- ImageGrab.grab() blocks - does it affect window polling?
- Should screenshot capture run in separate thread?

### 6. Edge Cases
- **Minimized windows:** Skip screenshot if window minimized?
- **Screensaver/lock screen:** Detect and skip?
- **Multi-monitor:** Does GetWindowRect() handle correctly?
- **Window partially off-screen:** Handle gracefully?

## Research Resources

**Image hashing:**
- http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
- https://github.com/JohannesBuchner/imagehash
- https://content-blockchain.org/research/testing-different-image-hash-functions/ (comparison)

**Python screenshot capture:**
- https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html
- https://stackoverflow.com/questions/19695214/python-screenshot-of-inactive-window-printwindow-win32gui

**Perceptual hashing papers:**
- "Perceptual Hashing: A Survey" - https://link.springer.com/chapter/10.1007/978-3-319-48896-7_2

## Environment Context
- **Development:** WSL2 Ubuntu (cannot test Windows APIs directly)
- **Target:** Windows 11
- **Dependencies:** pywin32, psutil, pystray, Pillow (all already installed)
- **Python:** 3.11+

## Deliverable
Provide:
1. **Critical review** of proposed approach (flaws, edge cases, gotchas)
2. **Algorithm recommendation** (pHash vs dHash vs alternative)
3. **Optimized threshold** for similarity comparison
4. **Database schema recommendation**
5. **Performance optimization suggestions**
6. **Any additional considerations** not covered above

Focus on robustness and real-world performance. Personal project = simplicity preferred over enterprise-grade complexity.
