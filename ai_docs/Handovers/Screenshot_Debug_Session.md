# Screenshot Capture Not Working - Debug Session Handover

## Current State
App runs, ScreenshotWorker initializes, but no screenshots are being saved to `%LOCALAPPDATA%\TimeLogger\screenshots`. The folder exists but is empty.

## Console Output (Last Run)
```
ScreenshotWorker initialized: C:\Users\Brahm\AppData\Local\TimeLogger\screenshots
Screenshot worker initialized
TrackerLoop initialized: poll=1.0s, idle_threshold=180s, merge_threshold=2.0s, screenshot_enabled=True
Tracking started
```
**Missing**: No "Screenshot submitted" or "Screenshot captured" messages appear after waiting.

## What Was Fixed This Session
1. **View Captured Images button not visible** - Fixed by reordering `pack()` calls in `__main__.py:322-342`. Button frame now packs before treeview.
2. **Moved button to top** - User requested, changed `side=tk.BOTTOM` to `side=tk.TOP`
3. **Added diagnostic logging** in `screenshot.py` - submit(), capture, save operations now log at INFO level

## The Bug Location
Screenshot submission happens in `tracker.py:226-230`:
```python
if self.screenshot_worker and WINDOWS_APIS_AVAILABLE:
    current_time = time.time()
    if current_time - self.last_screenshot_time >= self.screenshot_interval:
        self._submit_screenshot(window, idle_seconds)
        self.last_screenshot_time = current_time
```

Since no "Screenshot submitted" logs appear, one of these is failing:
- `self.screenshot_worker` is None (unlikely - init log shows it was created)
- `WINDOWS_APIS_AVAILABLE` is False in tracker.py (different from screenshot.py's variable!)
- `self.screenshot_interval` check never passes
- `_submit_screenshot()` throws before logging

## Key Insight: Two Different WINDOWS_APIS_AVAILABLE Variables
- `tracker.py:28` defines its own: checks for win32gui, win32process, psutil
- `screenshot.py:41` defines another: checks for win32gui, ImageGrab, AND PIL_AVAILABLE (which requires imagehash)

The tracker.py check at line 226 uses tracker.py's variable. If that's False, screenshots silently won't submit.

## Next Debug Steps
1. Add logging in `tracker.py` around line 226 to confirm WINDOWS_APIS_AVAILABLE value
2. Or add: `logging.info(f"Screenshot check: worker={self.screenshot_worker is not None}, apis={WINDOWS_APIS_AVAILABLE}")`
3. Verify `imagehash` is installed: `pip show imagehash`

## Key Files
| File | Purpose |
|------|---------|
| `lawtime/tracker.py:226-230` | Screenshot submission trigger point |
| `lawtime/tracker.py:323-349` | `_submit_screenshot()` method |
| `lawtime/screenshot.py:125-155` | `ScreenshotWorker.submit()` |
| `lawtime/screenshot.py:157-240` | `_capture_and_compare()` - actual capture logic |
| `lawtime/__main__.py:92-113` | Worker initialization and TrackerLoop setup |

## Red Herrings (Skip These)
- `lawtime/exporter.py` - JSON export, unrelated
- `lawtime/tray.py` - System tray UI only
- `test_*.py` - Old API verification scripts, not unit tests
- `ai_docs/compass_artifact_*.md` - Commercial product comparisons

## User's Environment
- Windows 11
- Project path: `C:\Users\Brahm\Git\TimeLogger`
- Data path: `C:\Users\Brahm\AppData\Local\TimeLogger\`
- Running via: `venv\Scripts\activate` then `python -m lawtime`

## Branch
`claude/enhance-screenshot-testing-01Wh5ejiuNiSQBcevB8RP3Kj`

## Commits Made This Session
1. `5123658` - Fix View Captured Images button not visible (pack order)
2. `47f55ce` - Move button to top of window
3. `07adec9` - Add diagnostic logging for screenshot capture
