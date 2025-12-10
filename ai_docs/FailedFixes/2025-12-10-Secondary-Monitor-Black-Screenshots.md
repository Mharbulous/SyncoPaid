# Failed Fix: Secondary Monitor Black Screenshots

**Date**: 2025-12-10
**Commit**: bc46d54d49dabb43bcad7cdc453e6567fa75f439
**Issue**: Screenshots captured from windows on secondary monitor (monitor #2) were being saved as completely black images

---

## Problem Description

When the application attempted to capture screenshots of active windows displayed on a secondary monitor, the resulting images were completely black instead of showing the actual window content. This issue only affected secondary monitors; primary monitor captures worked correctly.

## Attempted Fix

**Commit Message**: "Enhance screenshot capture for multi-monitor support by adjusting cropping coordinates based on virtual screen bounds."

### Implementation Details

The fix modified `lawtime/screenshot.py` in the `_capture_window()` method (lines 321-342):

**Original approach (failed)**:
```python
# Direct bbox capture
img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
```

**New approach (also failed)**:
```python
# Capture entire virtual screen space
img = ImageGrab.grab(all_screens=True)

# Get virtual screen bounds using Windows API
from ctypes import windll
virtual_screen_left = windll.user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
virtual_screen_top = windll.user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN

# Convert window coordinates to image coordinates
crop_left = x1 - virtual_screen_left
crop_top = y1 - virtual_screen_top
crop_right = x2 - virtual_screen_left
crop_bottom = y2 - virtual_screen_top

# Crop to the window region
img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
```

### Rationale

The fix was based on the following understanding:

1. **Multi-monitor coordinate system**: Windows uses a virtual screen coordinate system where secondary monitors may have positive or negative coordinates relative to the primary monitor
2. **ImageGrab limitation**: The `ImageGrab.grab(bbox=...)` method may not correctly handle coordinates outside the primary monitor's bounds
3. **Proposed solution**:
   - Capture the entire virtual screen using `all_screens=True`
   - Use Windows API to get the virtual screen origin (`SM_XVIRTUALSCREEN`, `SM_YVIRTUALSCREEN`)
   - Translate window coordinates from virtual screen space to image space
   - Crop the full capture to the desired window region

### Why It Was Expected to Work

- `ImageGrab.grab(all_screens=True)` is documented to capture all monitors in a multi-monitor setup
- The Windows System Metrics API (`GetSystemMetrics(76)` and `GetSystemMetrics(77)`) correctly report the virtual screen bounds
- The coordinate transformation math appeared sound: subtracting the virtual screen origin from window coordinates should give the correct image pixel coordinates

---

## Why It Failed

Despite the logical approach, the fix did not resolve the black screenshot issue on secondary monitors. Possible reasons include:

### Hypothesis 1: Pillow/ImageGrab Bug with Windows DPI/Scaling
- Secondary monitors may have different DPI scaling settings
- ImageGrab may not correctly handle DPI-aware coordinates in multi-monitor setups
- The `all_screens=True` capture may not properly handle mixed DPI scenarios

### Hypothesis 2: Window Composition/DWM Issues
- Windows Desktop Window Manager (DWM) may not allow cross-monitor screenshot capture via PIL
- DirectX/GPU-accelerated windows on secondary monitors may require different capture APIs
- Window layering or transparency effects may interact differently on secondary monitors

### Hypothesis 3: Coordinate System Mismatch
- Although the math appears correct, there may be additional coordinate transformations needed
- Virtual screen coordinates from `GetWindowRect()` may not match the coordinate system used by `ImageGrab.grab(all_screens=True)`
- High DPI awareness settings may cause coordinate scaling issues

### Hypothesis 4: Timing/Race Condition
- The window may lose focus or change state during the capture-then-crop process
- The two-step process (full capture + crop) may be slower than direct bbox capture, causing issues

---

## Observations

1. The fix successfully captures *something* using `all_screens=True` (no exceptions thrown)
2. The cropping logic executes without errors
3. The resulting image is saved, but contains only black pixels
4. The issue is specific to secondary monitors - primary monitor still works

---

## Alternative Approaches to Consider

### Option 1: Windows Graphics Capture API
Use the newer Windows.Graphics.Capture API (available Windows 10 1803+) which is designed for reliable window/monitor capture:
```python
import Windows.Graphics.Capture  # Requires pywinrt
```

### Option 2: Win32 BitBlt API
Use lower-level Win32 APIs directly instead of PIL:
```python
import win32ui
import win32gui
import win32con
# Use BitBlt with source and destination DCs
```

### Option 3: MSS Library
Replace PIL ImageGrab with the `mss` library, which has better multi-monitor support:
```python
import mss
with mss.mss() as sct:
    monitor = {"left": x1, "top": y1, "width": width, "height": height}
    img = sct.grab(monitor)
```

### Option 4: DPI-Aware Coordinate Adjustment
Explicitly handle DPI scaling using `SetProcessDPIAware()` and scale coordinates:
```python
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
```

### Option 5: Per-Monitor Investigation
Add diagnostic logging to determine if specific monitor properties correlate with failures:
- Monitor index/ID
- Resolution
- DPI scaling factor
- Color depth
- Graphics adapter

---

## Next Steps

1. **Add diagnostic logging** to capture:
   - Virtual screen bounds
   - Window rect coordinates
   - Crop coordinates
   - Resulting image dimensions
   - Monitor on which window is displayed

2. **Test alternative capture libraries** (mss, win32ui) on secondary monitor

3. **Verify DPI awareness** settings for the application

4. **Consider per-monitor capture** instead of virtual screen crop approach

5. **Test with different monitor arrangements** (left/right/above/below primary)

---

## References

- Commit: bc46d54d49dabb43bcad7cdc453e6567fa75f439
- File: `lawtime/screenshot.py` lines 321-342
- Related Windows API:
  - `SM_XVIRTUALSCREEN` (76): Left coordinate of virtual screen
  - `SM_YVIRTUALSCREEN` (77): Top coordinate of virtual screen
  - `win32gui.GetWindowRect()`: Window coordinates in virtual screen space
