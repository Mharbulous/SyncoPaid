# TimeLogger Project Handover

## Project Summary

Building a Windows 11 desktop app for a civil litigation lawyer to automatically track computer activity for legal billing. Python, local-only storage, JSON export for external LLM categorization. MVP scope: capture only, no AI integration yet.

## Key Project Files

**Read these first:**
- `LawTime_Tracker_PRD.md` — Full requirements, data model, SQLite schema, working code snippets for window capture and idle detection
- `LawTime_Setup_Guide.md` — Environment setup, three test scripts to verify APIs, project structure, Claude Code workflow

**Background research (reference only if needed):**
- `Building_a_Windows_11_Lawyer_Time_Tracker__Requirements_and_Open_Source_Foundations.md` — Open source analysis
- `compass_artifact_wf-*.md` files — Commercial tool comparisons (TimeCamp alternatives, AI time tracking)

## Red Herrings to Ignore

**Do NOT fork ActivityWatch.** The research documents recommend it, but this was rejected after deeper analysis:
- ActivityWatch requires running a REST server (aw-server) on port 5600
- The aw-client library only works with the server running—not standalone
- Multi-process architecture is overkill for this MVP
- The actual tracking code is ~50 lines; ActivityWatch's complexity is in features we don't need

**Other dead ends:**
- Selfspy — Dead project (last update 2019), Python 2.7 only
- time-on-fire — Too minimal, no window titles, no idle detection

## Decided Approach

**Build from scratch**, referencing ActivityWatch's code patterns for:
- Window title capture via `win32gui.GetForegroundWindow()`
- Idle detection via `GetLastInputInfo` Windows API
- Event merging logic

The PRD Section 9 contains working implementations of both core functions.

## Technical Stack (decided)

```
Python 3.11+
pywin32 — Window titles, process detection
psutil — Process name resolution  
ctypes — Idle detection (GetLastInputInfo)
SQLite — Local storage (stdlib)
pystray + Pillow — System tray
tkinter — File dialogs (stdlib)
```

## Key Technical Insights

**Window tracking on Windows 11:**
- `win32gui.GetForegroundWindow()` returns handle
- `win32gui.GetWindowText(hwnd)` returns title
- `win32process.GetWindowThreadProcessId(hwnd)` returns PID
- May need `python -m pywin32_postinstall -install` after pip install

**Idle detection:**
- Windows `GetLastInputInfo` API via ctypes
- Returns milliseconds since last keyboard/mouse input
- Threshold: 180 seconds (configurable)

**Outlook limitation (known issue):**
- New Outlook doesn't expose email subjects in window titles
- Legacy Outlook does
- Microsoft may fix by late 2025
- Not blocking for MVP—just capture what's available

## Useful URLs

- ActivityWatch architecture (reference patterns, don't fork): https://github.com/ActivityWatch/activitywatch
- aw-watcher-window source (window capture patterns): https://github.com/ActivityWatch/aw-watcher-window
- pystray documentation: https://pystray.readthedocs.io/
- Writing ActivityWatch watchers (shows aw-client API): https://docs.activitywatch.net/en/latest/examples/writing-watchers.html

## Development Sequence

1. `tracker.py` — Window capture + idle detection loop
2. `database.py` — SQLite storage
3. `config.py` — Settings management
4. `exporter.py` — JSON export
5. `tray.py` — System tray UI
6. `__main__.py` — Wire together

## Current Status

- PRD complete
- Setup guide complete  
- Project structure defined
- **Next:** User runs test scripts on their Windows 11 machine, then begins tracker.py implementation

## Notes

- App renamed from "LawTime" to "TimeLogger"
- User is a lawyer with hobbyist Python experience
- Vibe coding with Claude Code—keep code straightforward
- All data must stay local (attorney-client privilege)
