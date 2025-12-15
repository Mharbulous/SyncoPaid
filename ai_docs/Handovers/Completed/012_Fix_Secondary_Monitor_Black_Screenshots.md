# Handover: Fix Secondary Monitor Black Screenshots

## Issue
Screenshots captured from windows on secondary monitor (monitor #2) are saved as completely black images. Primary monitor captures work correctly.

## Failed Fix (Commit bc46d54)
**Approach**: Virtual screen coordinate transformation using `ImageGrab.grab(all_screens=True)` + crop

**What was tried** in `lawtime/screenshot.py` lines 321-342:
```python
# Capture entire virtual screen
img = ImageGrab.grab(all_screens=True)

# Get virtual screen bounds
virtual_screen_left = windll.user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
virtual_screen_top = windll.user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN

# Translate coords and crop
crop_left = x1 - virtual_screen_left
crop_top = y1 - virtual_screen_top
crop_right = x2 - virtual_screen_left
crop_bottom = y2 - virtual_screen_top
img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
```

**Why it failed**: Still produced black images on monitor #2. Likely PIL/Pillow bug with multi-monitor bbox handling (known issue in Pillow #1547, #7898).

**Documentation**: Full analysis in `ai_docs/FailedFixes/2025-12-10-Secondary-Monitor-Black-Screenshots.md`

## Key Files

| File | Status | Notes |
|------|--------|-------|
| `lawtime/screenshot.py` | **AFFECTED** | Periodic screenshots, lines 272-348 `_capture_window()` method has failed fix |
| `lawtime/action_screenshot.py` | **AFFECTED** | Action screenshots, lines 408-450 `_capture_window()` still uses old direct bbox (line 450: `ImageGrab.grab(bbox=(x1, y1, x2, y2))`) |
| `ai_docs/FailedFixes/2025-12-10-Secondary-Monitor-Black-Screenshots.md` | Reference | Complete failed fix analysis, hypotheses, alternatives |

**IMPORTANT**: Both files have separate `_capture_window()` implementations. Both need fixing.

## Not Relevant (Red Herrings)
- `lawtime/tracker.py` - Only submits screenshot requests, doesn't capture
- `lawtime/database.py` - Stores screenshots, doesn't capture them
- `diagnose_screenshots.py` - Diagnostic tool, not part of capture flow
- DPI settings/scaling - Unlikely root cause (Windows API reports correct coords)

## Technical Context from Research

### Root Cause (PIL/Pillow Bug)
PIL's `ImageGrab.grab(bbox=...)` fails when bbox coordinates are outside primary monitor bounds. This is a **known bug** tracked in Pillow GitHub issues:
- [Pillow #1547: ImageGrab fails with multiple monitors](https://github.com/python-pillow/Pillow/issues/1547)
- [Pillow #7898: ImageGrab unable to capture with bbox when external monitor attached](https://github.com/python-pillow/Pillow/issues/7898)

**Technical detail**: `ImageGrab.grab()` retrieves a DC handle to entire desktop, but subsequent `GetDeviceCaps(HORZRES/VERTRES)` calls only return primary monitor dimensions, not full virtual screen.

### Proven Alternative Solutions (Priority Order)

#### Option 1: MSS Library (Recommended - Fast & Simple)
**Library**: `python-mss` (pure Python, no dependencies, cross-platform, thread-safe)
- [MSS Documentation](https://python-mss.readthedocs.io/)
- [MSS Examples](https://python-mss.readthedocs.io/examples.html)
- [MSS GitHub](https://github.com/BoboTiG/python-mss)
- [Nitratine MSS Tutorial](https://nitratine.net/blog/post/how-to-take-a-screenshot-in-python-using-mss/)

**Usage**:
```python
import mss
with mss.mss() as sct:
    # monitors[0] = all monitors combined
    # monitors[1] = first monitor, monitors[2] = second monitor, etc.
    monitor = {"left": x1, "top": y1, "width": width, "height": height}
    screenshot = sct.grab(monitor)
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
```

**Why this works**: MSS uses Windows API directly (via ctypes) and handles multi-monitor coordinate systems correctly.

#### Option 2: D3DShot (Fastest, DirectX-based)
**Library**: `d3dshot` (Windows 8.1+, GPU-accelerated)
- [D3DShot PyPI](https://pypi.org/project/d3dshot/)

**Why this works**: Uses DirectX, detects displays in any configuration. Fastest capture method on Windows.

**Caveat**: More dependencies, DirectX-specific.

#### Option 3: Win32 BitBlt API (Manual, Full Control)
**Resources**:
- [Learn Code By Gaming - Fast Window Capture](https://learncodebygaming.com/blog/fast-window-capture)
- [Microsoft Docs - Capturing an Image](https://learn.microsoft.com/en-us/windows/win32/gdi/capturing-an-image)
- [Desktopmagic win32 implementation](https://github.com/ludios/Desktopmagic/blob/master/desktopmagic/screengrab_win32.py)

**Pattern**:
```python
import win32gui, win32ui, win32con
hwndDC = win32gui.GetWindowDC(hwnd)
mfcDC = win32ui.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()
saveBitMap = win32ui.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
saveDC.SelectObject(saveBitMap)
saveDC.BitBlt((0, 0), (width, height), mfcDC, (x1, y1), win32con.SRCCOPY)
```

**Note**: Handles negative coordinates for monitors left/above primary.

#### Option 4: Desktopmagic Library
**Library**: `Desktopmagic` (Windows-specific, robust)
- [Desktopmagic GitHub](https://github.com/ludios/Desktopmagic)

**Why this works**: Built specifically for multi-monitor Windows setups. Can capture all monitors, entire virtual screen, or split into one PIL Image per display.

## Recommended Approach

**Use MSS Library** (Option 1) because:
1. Pure Python, minimal dependencies
2. Cross-platform (preserves future macOS/Linux compatibility)
3. Thread-safe (important for async ScreenshotWorker)
4. Well-maintained, widely used
5. Proven to handle multi-monitor correctly
6. Simple drop-in replacement for ImageGrab

## Implementation Steps

1. **Add dependency**: Add `mss` to `requirements.txt`
2. **Update both files**:
   - `lawtime/screenshot.py` line 321-342
   - `lawtime/action_screenshot.py` line 450
3. **Import MSS**: Add `import mss` at top of both files
4. **Replace `_capture_window()` capture logic**:
   - Remove `ImageGrab.grab()` calls
   - Replace with MSS capture code
   - Convert MSS screenshot to PIL Image
5. **Test on Windows 11**: Requires testing on actual Windows machine with monitor #2
6. **Add diagnostic logging**: Log monitor coords, virtual screen bounds for debugging

## Edge Cases to Test
- Window spanning multiple monitors (capture primary monitor region)
- Monitor positioned left/above primary (negative coordinates)
- Different DPI scaling on monitors
- Window partially off-screen

## Branch
`claude/fix-secondary-monitor-screenshots-01JGXVojok5P9BoSrqzUjzUS`

## Test Requirements
**CRITICAL**: This cannot be tested in Claude Code web environment (Linux sandbox, no Windows APIs). Must be tested on:
- **Platform**: Windows 11
- **Location**: `C:\Users\Brahm\Git\TimeLogger`
- **Setup**: Multi-monitor with monitor #2 active
- **Test**: Capture window on monitor #2, verify screenshot not black

## Success Criteria
Screenshots of windows on secondary monitor save as actual window content, not black images.
