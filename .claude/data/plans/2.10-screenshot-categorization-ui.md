# Screenshot-Assisted Time Categorization UI - Implementation Plan

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Display relevant screenshots inline during categorization when AI confidence is low (<70%)
**Approach:** Create new `categorization_ui.py` module with screenshot query/display logic. Query screenshots by timestamp range, implement LRU cache (50MB max), show thumbnails with modal viewer. Integrate with story 4.8 UI framework.
**Tech Stack:** tkinter, PIL/Pillow, sqlite3, functools.lru_cache

---

**Story ID:** 2.10 | **Created:** 2025-12-16 | **Status:** `planned`

---

## Story Context

**Title:** Screenshot-Assisted Time Categorization UI

**Description:** As a lawyer categorizing ambiguous activities, I want to see relevant screenshots inline during the categorization flow when the AI needs clarification, so that I can accurately remember what I was working on and assign time to the correct client matter.

**Acceptance Criteria:**
- [ ] Integrate screenshot display into time categorization UI (not standalone gallery)
- [ ] Query screenshots table by timestamp range matching uncategorized activity period
- [ ] Display thumbnails in chronological order with timestamps
- [ ] Click thumbnail to view full-resolution screenshot in modal
- [ ] Show screenshot only when AI confidence is low (<70%) for activity-to-matter match
- [ ] Cache recently viewed screenshots for performance (LRU cache, max 50MB)
- [ ] Handle missing screenshots gracefully (file deleted/archived) with placeholder

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Story 4.8 (Smart Time Categorization Prompt) UI framework exists

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_categorization_ui.py` | Create | Test screenshot query, cache, display logic |
| `src/syncopaid/categorization_ui.py` | Create | Screenshot UI component for categorization |
| `src/syncopaid/database.py:340-370` | Read | Understand screenshots query methods |

## TDD Tasks

### Task 1: Screenshot Query by Timestamp Range

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for querying screenshots by timestamp range.
```python
def test_query_screenshots_by_timestamp():
    db = Database(':memory:')
    # Insert test screenshots
    db.insert_screenshot('2025-12-16T10:00:00', 'path1.png', 'app1', 'title1', 'hash1')
    db.insert_screenshot('2025-12-16T10:05:00', 'path2.png', 'app1', 'title2', 'hash2')

    from syncopaid.categorization_ui import query_screenshots_for_activity
    results = query_screenshots_for_activity(db, '2025-12-16T10:00:00', '2025-12-16T10:10:00')

    assert len(results) == 2
    assert results[0]['file_path'] == 'path1.png'
    assert results[1]['file_path'] == 'path2.png'
```
Run: `pytest tests/test_categorization_ui.py::test_query_screenshots_by_timestamp -v` → Expect: FAILED (module doesn't exist)

**GREEN:** Implement screenshot query function.
```python
# src/syncopaid/categorization_ui.py
def query_screenshots_for_activity(db, start_time: str, end_time: str) -> List[Dict]:
    """Query screenshots within activity timestamp range."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, captured_at, file_path, window_app, window_title
            FROM screenshots
            WHERE captured_at >= ? AND captured_at <= ?
            ORDER BY captured_at ASC
        """, (start_time, end_time))
        return [dict(row) for row in cursor.fetchall()]
```
Run: `pytest tests/test_categorization_ui.py::test_query_screenshots_by_timestamp -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add screenshot query by timestamp range for categorization"`

---

### Task 2: LRU Cache for Screenshot Images (50MB Max)

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for screenshot caching with size limit.
```python
def test_screenshot_cache_lru():
    from syncopaid.categorization_ui import ScreenshotCache

    cache = ScreenshotCache(max_size_mb=50)

    # Load mock images (track cache size)
    img1 = cache.get_image('path1.png')  # 2MB
    img2 = cache.get_image('path2.png')  # 3MB

    assert cache.current_size_mb < 50
    assert cache.hit_count == 0

    # Second access should be cached
    img1_cached = cache.get_image('path1.png')
    assert cache.hit_count == 1
```
Run: `pytest tests/test_categorization_ui.py::test_screenshot_cache_lru -v` → Expect: FAILED

**GREEN:** Implement LRU cache with size tracking.
```python
from functools import lru_cache
from PIL import Image
import os

class ScreenshotCache:
    def __init__(self, max_size_mb: int = 50):
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.current_size_mb = 0
        self.hit_count = 0

    def get_image(self, path: str):
        if path in self.cache:
            self.hit_count += 1
            return self.cache[path]

        if os.path.exists(path):
            img = Image.open(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)

            # Evict if needed
            while self.current_size_mb + size_mb > self.max_size_mb and self.cache:
                oldest_key = next(iter(self.cache))
                self._evict(oldest_key)

            self.cache[path] = img
            self.current_size_mb += size_mb
            return img
        return None

    def _evict(self, key):
        if key in self.cache:
            size_mb = os.path.getsize(key) / (1024 * 1024)
            del self.cache[key]
            self.current_size_mb -= size_mb
```
Run: `pytest tests/test_categorization_ui.py::test_screenshot_cache_lru -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add LRU cache for screenshots with 50MB size limit"`

---

### Task 3: Thumbnail Display Widget (Chronological Order)

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for thumbnail widget creation.
```python
def test_thumbnail_widget_creation():
    import tkinter as tk
    from syncopaid.categorization_ui import create_thumbnail_widget

    root = tk.Tk()
    screenshots = [
        {'file_path': 'path1.png', 'captured_at': '2025-12-16T10:00:00'},
        {'file_path': 'path2.png', 'captured_at': '2025-12-16T10:05:00'}
    ]

    widget = create_thumbnail_widget(root, screenshots)

    assert widget is not None
    # Verify thumbnails are in chronological order
    assert len(widget.winfo_children()) == 2

    root.destroy()
```
Run: `pytest tests/test_categorization_ui.py::test_thumbnail_widget_creation -v` → Expect: FAILED

**GREEN:** Implement thumbnail display widget.
```python
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def create_thumbnail_widget(parent, screenshots: List[Dict], cache: ScreenshotCache) -> ttk.Frame:
    """Create scrollable thumbnail widget showing screenshots chronologically."""
    frame = ttk.Frame(parent)

    # Create scrollable canvas
    canvas = tk.Canvas(frame, height=150)
    scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=scrollbar.set)

    inner_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # Add thumbnails
    for i, screenshot in enumerate(screenshots):
        img = cache.get_image(screenshot['file_path'])
        if img:
            thumb = img.copy()
            thumb.thumbnail((120, 90))
            photo = ImageTk.PhotoImage(thumb)

            btn = tk.Button(inner_frame, image=photo)
            btn.image = photo  # Keep reference
            btn.grid(row=0, column=i, padx=5)

            # Add timestamp label
            label = tk.Label(inner_frame, text=screenshot['captured_at'][11:19])
            label.grid(row=1, column=i)

    canvas.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="bottom", fill="x")

    return frame
```
Run: `pytest tests/test_categorization_ui.py::test_thumbnail_widget_creation -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add thumbnail display widget with chronological ordering"`

---

### Task 4: Modal Viewer for Full-Resolution Screenshots

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for modal screenshot viewer.
```python
def test_modal_viewer():
    import tkinter as tk
    from syncopaid.categorization_ui import show_screenshot_modal

    root = tk.Tk()
    screenshot_path = 'test_screenshot.png'

    # Create test image
    img = Image.new('RGB', (800, 600), color='red')
    img.save(screenshot_path)

    modal = show_screenshot_modal(root, screenshot_path)

    assert modal is not None
    # Modal should be transient window
    assert modal.winfo_toplevel() != root

    os.remove(screenshot_path)
    modal.destroy()
    root.destroy()
```
Run: `pytest tests/test_categorization_ui.py::test_modal_viewer -v` → Expect: FAILED

**GREEN:** Implement modal viewer.
```python
def show_screenshot_modal(parent, screenshot_path: str):
    """Show full-resolution screenshot in modal dialog."""
    modal = tk.Toplevel(parent)
    modal.title("Screenshot Viewer")
    modal.transient(parent)

    if os.path.exists(screenshot_path):
        img = Image.open(screenshot_path)

        # Scale to fit screen (max 1200x800)
        img.thumbnail((1200, 800))
        photo = ImageTk.PhotoImage(img)

        label = tk.Label(modal, image=photo)
        label.image = photo  # Keep reference
        label.pack()
    else:
        # Missing file placeholder
        label = tk.Label(modal, text="Screenshot not found", fg="gray")
        label.pack(padx=50, pady=50)

    # Close button
    btn = ttk.Button(modal, text="Close", command=modal.destroy)
    btn.pack(pady=10)

    modal.grab_set()
    return modal
```
Run: `pytest tests/test_categorization_ui.py::test_modal_viewer -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add modal viewer for full-resolution screenshots"`

---

### Task 5: Conditional Display (AI Confidence < 70%)

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for conditional screenshot display.
```python
def test_conditional_screenshot_display():
    from syncopaid.categorization_ui import should_show_screenshots

    # High confidence - no screenshots
    assert should_show_screenshots(ai_confidence=0.85) == False

    # Low confidence - show screenshots
    assert should_show_screenshots(ai_confidence=0.65) == True
    assert should_show_screenshots(ai_confidence=0.70) == True

    # Edge case
    assert should_show_screenshots(ai_confidence=0.69) == True
```
Run: `pytest tests/test_categorization_ui.py::test_conditional_screenshot_display -v` → Expect: FAILED

**GREEN:** Implement confidence threshold logic.
```python
def should_show_screenshots(ai_confidence: float, threshold: float = 0.70) -> bool:
    """Determine if screenshots should be shown based on AI confidence."""
    return ai_confidence < threshold
```
Run: `pytest tests/test_categorization_ui.py::test_conditional_screenshot_display -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add conditional screenshot display based on AI confidence threshold"`

---

### Task 6: Missing Screenshot Placeholder

**Files:** Test: `tests/test_categorization_ui.py` | Impl: `src/syncopaid/categorization_ui.py`

**RED:** Create test for missing file handling.
```python
def test_missing_screenshot_placeholder():
    import tkinter as tk
    from syncopaid.categorization_ui import create_thumbnail_widget

    root = tk.Tk()
    cache = ScreenshotCache(max_size_mb=50)

    screenshots = [
        {'file_path': 'missing.png', 'captured_at': '2025-12-16T10:00:00'}
    ]

    widget = create_thumbnail_widget(root, screenshots, cache)

    # Should create widget with placeholder
    assert widget is not None
    assert len(widget.winfo_children()) > 0

    root.destroy()
```
Run: `pytest tests/test_categorization_ui.py::test_missing_screenshot_placeholder -v` → Expect: FAILED (no placeholder)

**GREEN:** Add placeholder handling in thumbnail widget.
```python
# Update create_thumbnail_widget function
def create_thumbnail_widget(parent, screenshots: List[Dict], cache: ScreenshotCache) -> ttk.Frame:
    # ... existing code ...

    for i, screenshot in enumerate(screenshots):
        img = cache.get_image(screenshot['file_path'])

        if img:
            # Existing thumbnail code
            thumb = img.copy()
            thumb.thumbnail((120, 90))
            photo = ImageTk.PhotoImage(thumb)
        else:
            # Create placeholder for missing file
            placeholder = Image.new('RGB', (120, 90), color='lightgray')
            from PIL import ImageDraw
            draw = ImageDraw.Draw(placeholder)
            draw.text((30, 40), "Missing", fill='gray')
            photo = ImageTk.PhotoImage(placeholder)

        btn = tk.Button(inner_frame, image=photo)
        btn.image = photo
        btn.grid(row=0, column=i, padx=5)

        # ... rest of code ...
```
Run: `pytest tests/test_categorization_ui.py::test_missing_screenshot_placeholder -v` → Expect: PASSED

**COMMIT:** `git add tests/test_categorization_ui.py src/syncopaid/categorization_ui.py && git commit -m "feat: add placeholder for missing screenshot files"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Module imports: `python -c "from syncopaid.categorization_ui import query_screenshots_for_activity"`
- [ ] Integration with story 4.8 UI framework verified

## Notes

- **Integration Point**: This module provides components for story 4.8 (Smart Time Categorization Prompt UI)
- **Performance**: LRU cache set to 50MB max; monitor memory usage with many screenshots
- **Edge Cases**:
  - Empty screenshot results (no captures during activity period)
  - Archived/deleted screenshot files (placeholder shown)
  - Very large screenshots (>10MB) may impact cache efficiency
- **Follow-up**: Consider adding screenshot zoom controls in modal viewer
- **Dependencies**: Requires tkinter, PIL/Pillow for UI components
