# TimeLogger Project - Session 1 Progress Report

**Date:** December 9, 2025  
**Status:** Environment verified, ready for implementation

---

## ✅ Completed

### Environment Setup
- **Location:** `C:\Users\Brahm\Git\TimeLogger`
- **Python:** 3.13.7 (in virtual environment)
- **Terminal:** VS Code with Windows PowerShell 5.1
- **Dependencies installed:**
  - pywin32 (v311)
  - psutil (v7.1.3)
  - pystray (v0.19.5)
  - Pillow (v12.0.0)

### Test Results - All Pass

**Test 1: Window Tracking (`test_window.py`)**
- ✅ Successfully captures foreground window titles
- ✅ Detects application names (Chrome, Outlook, Word, etc.)
- ✅ Updates in real-time when switching windows

**Test 2: Idle Detection (`test_idle.py`)**
- ✅ GetLastInputInfo API working correctly
- ✅ Tracks seconds since last keyboard/mouse input
- ✅ Resets to zero on any user activity

**Test 3: System Tray Icon (`test_tray.py`)**
- ✅ Green circle icon displays in Windows system tray
- ✅ Right-click menu functional
- ✅ Tooltip shows correctly

### Real-World App Testing

**Apps with good title capture:**
- ✅ **Outlook** - Email subjects (when opened in separate windows)
- ✅ **Chrome** - Page titles including URLs
- ✅ **Word** - Document filenames visible
- ✅ **CanLII** - Case names and citations appear

**Known Limitations (Expected):**
- ⚠️ **Outlook reading pane** - Shows generic "Inbox" title instead of individual email subjects
  - Affects all automatic time trackers (architectural limitation)
  - Workaround: Open emails in separate windows
  - Microsoft may fix by late 2025
- ⚠️ **Some websites** - Generic titles like "Dashboard" or "Home"
  - Future enhancement: Capture URLs alongside titles

---

## 📁 Project Structure (Created)

```
C:\Users\Brahm\Git\TimeLogger/
├── venv/                    # Virtual environment (active)
├── test_window.py           # Window capture test (working)
├── test_idle.py            # Idle detection test (working)  
└── test_tray.py            # System tray test (working)
```

**Not yet created:**
```
lawtime/                    # Main package (next step)
├── __init__.py
├── __main__.py
├── tracker.py             # ← START HERE
├── database.py
├── exporter.py
├── tray.py
└── config.py
```

---

## 🎯 Next Session Goals

1. Create `lawtime/` package structure
2. Build `tracker.py` - Core monitoring loop that:
   - Combines window capture + idle detection
   - Polls every 1 second
   - Merges consecutive identical window states
   - Yields event dictionaries for storage
3. Test tracker.py in console mode before integrating database

---

## 📝 Key Insights

### pywin32 Post-Install
- Command `python -m pywin32_postinstall -install` failed with "No module named pywin32_postinstall"
- This is **not a problem** - window tracking works despite the error
- Common issue with Python 3.13, pywin32 v311

### Outlook Behavior
- **Opening emails in separate windows** = Subject captured ✅
- **Reading pane preview** = Generic "Inbox" title ⚠️
- User should adopt habit of double-clicking important emails

### CanLII Research Time
- Case names and citations appear in window titles when viewing cases
- This provides sufficient granularity for matter attribution

---

## 🔧 Technical Notes

### Window Capture Pattern (Verified Working)
```python
import win32gui
import win32process
import psutil

hwnd = win32gui.GetForegroundWindow()
title = win32gui.GetWindowText(hwnd)
_, pid = win32process.GetWindowThreadProcessId(hwnd)
process = psutil.Process(pid).name()
```

### Idle Detection Pattern (Verified Working)
```python
from ctypes import Structure, windll, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]

def get_idle_seconds():
    info = LASTINPUTINFO()
    info.cbSize = sizeof(info)
    windll.user32.GetLastInputInfo(byref(info))
    millis = windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0
```

### System Tray Pattern (Verified Working)
```python
import pystray
from PIL import Image, ImageDraw

# Create 64x64 circle icon
# Use pystray.Menu with MenuItem for right-click menu
# icon.run() blocks until icon.stop() called
```

---

## 📚 Reference Documents

**Primary requirements:**
- `LawTime_Tracker_PRD.md` - Complete specification, data model, SQLite schema
- `LawTime_Setup_Guide.md` - Environment setup (completed)

**Background research (reference only):**
- `Building_a_Windows_11_Lawyer_Time_Tracker__Requirements_and_Open_Source_Foundations.md`
- `compass_artifact_wf-*.md` files - Commercial tool comparisons

**Project renamed:** "LawTime" → "TimeLogger"

---

## ⚠️ Critical Decision: Do NOT Fork ActivityWatch

The research documents recommend forking ActivityWatch, but this was **rejected** after analysis:
- Requires running REST server (aw-server) on port 5600
- aw-client library only works with server running
- Multi-process architecture is overkill for MVP
- Actual tracking code is ~50 lines; ActivityWatch's complexity is in features we don't need

**Approach:** Build from scratch, reference ActivityWatch's patterns for window/idle detection only.

---

## 🎓 User Context

- Civil litigation lawyer in Vancouver, BC
- Python hobbyist experience level
- Uses Outlook, Chrome, Word, CanLII, court websites
- Needs attorney-client privilege (local-only storage critical for MVP)
- Future: Will connect to online AI categorization service (not in MVP)
