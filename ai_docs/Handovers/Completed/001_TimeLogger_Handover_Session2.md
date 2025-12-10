# TimeLogger Implementation - Session 2 Handover

## Context
Building Windows 11 automatic time tracker for civil litigation lawyer. Python 3.13.7, VS Code terminal, all APIs verified working. Ready to implement core tracking module.

## Project State
**Location:** `C:\Users\Brahm\Git\TimeLogger`  
**Environment:** Virtual environment active, dependencies installed (pywin32, psutil, pystray, Pillow)  
**Tests passing:** Window capture, idle detection, system tray all verified on user's machine

## Core Requirements (from PRD)
- Poll every 1 second for active window title + app name
- Detect idle (180s threshold default)
- Merge consecutive identical window states into single events
- Store in local SQLite: `events(id, timestamp, duration_seconds, app, title, url, is_idle)`
- Export to JSON for external LLM processing
- System tray UI (start/pause/export/quit)
- **Critical:** Local-only storage (attorney-client privilege)
- **Future:** Will connect to online AI service (not MVP)

## Key Files to Read

**Primary specs (read these first):**
- `/mnt/project/LawTime_Tracker_PRD.md` - Complete requirements, data model, working code snippets in Section 9
- `/mnt/project/TimeLogger_Progress_Session1.md` - Session 1 results, test outcomes, verified patterns

**Reference only if needed:**
- `/mnt/project/LawTime_Setup_Guide.md` - Setup already complete
- `/mnt/project/Building_a_Windows_11_Lawyer_Time_Tracker__Requirements_and_Open_Source_Foundations.md` - Research on open source options

**Ignore these (red herrings):**
- `/mnt/project/compass_artifact_wf-*.md` files - Commercial tool comparisons, not relevant to implementation

## Critical Decisions Already Made

### ❌ Do NOT Fork ActivityWatch
Research docs recommend it, but **rejected** because:
- Requires REST server (aw-server:5600) running
- aw-client library depends on server
- Multi-process overhead unnecessary
- We only need ~50 lines of actual tracking code

**Approach:** Build from scratch, reference ActivityWatch patterns only.

### ❌ pywin32_postinstall Failed (Non-Issue)
`python -m pywin32_postinstall -install` returns "No module named pywin32_postinstall" but window tracking works fine anyway. Ignore this error.

### ✅ Verified Working Patterns

**Window capture:**
```python
import win32gui, win32process, psutil
hwnd = win32gui.GetForegroundWindow()
title = win32gui.GetWindowText(hwnd)
_, pid = win32process.GetWindowThreadProcessId(hwnd)
process = psutil.Process(pid).name()
```

**Idle detection:**
```python
from ctypes import Structure, windll, c_uint, sizeof, byref
class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]
# Use windll.user32.GetLastInputInfo + windll.kernel32.GetTickCount
```

## Known Limitations (Expected, Acceptable)

1. **Outlook reading pane** - Shows generic "Inbox" instead of email subjects
   - Only when using preview pane; separate windows work fine
   - Architectural limitation affecting all trackers
   - User will double-click important emails

2. **Some websites** - Generic titles like "Dashboard"
   - Future: Capture URLs alongside titles
   - MVP: Accept title-only granularity

3. **CanLII** - Actually works fine, case names appear in titles

## Implementation Plan

### Module 1: tracker.py (Start Here)
Build `TrackerLoop` class:
- `get_active_window()` - Returns `{app, title, pid}`
- `get_idle_seconds()` - Returns float
- Main loop: Poll → Detect changes → Merge consecutive → Yield events
- Console test mode before database integration

### Module 2: database.py
SQLite operations (schema in PRD Section 6.2):
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    app TEXT, title TEXT, url TEXT,
    is_idle INTEGER DEFAULT 0
);
```

### Module 3: config.py
JSON settings in `%LOCALAPPDATA%\TimeLogger\config.json` (defaults in PRD Section 8)

### Module 4: exporter.py  
Export events to JSON with date filtering (format in PRD Section 6.3)

### Module 5: tray.py
System tray icon (green=active, yellow=paused) with menu

### Module 6: __main__.py
Wire everything together

## Technical References

**ActivityWatch patterns (reference only, don't fork):**
- Window watcher: https://github.com/ActivityWatch/aw-watcher-window
- Event model: https://github.com/ActivityWatch/aw-core
- Architecture docs: https://docs.activitywatch.net/en/latest/

**Windows APIs:**
- GetLastInputInfo: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getlastinputinfo
- GetForegroundWindow: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow

**pystray library:**
- Docs: https://pystray.readthedocs.io/en/latest/
- GitHub: https://github.com/moses-palmer/pystray

## User Profile
- Civil litigation lawyer, Vancouver BC
- Python hobbyist level
- Uses: Outlook, Chrome, Word, CanLII, court websites
- Prefers: Straightforward code over clever abstractions
- Context: This will become a commercial product eventually (online AI service)

## Next Steps
1. Create `lawtime/` package structure (7 empty files)
2. Implement `tracker.py` with console test mode
3. Test tracking overnight for stability
4. Proceed to database → config → exporter → tray → main

## Questions to Resolve
- Event merging threshold: 2 seconds? (if window A → window B → window A within 2s, treat as continuous A)
- Idle threshold configurable: Default 180s, expose in config?
- Poll interval: 1 second sufficient? (balance between granularity and CPU usage)
