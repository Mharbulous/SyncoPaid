# TimeLogger Session 3 Handover

## Current State
**MVP complete, Git initialized, pushed to GitHub.** Ready for Windows testing.

**Repo:** https://github.com/Mharbulous/TimeLogger (private)
**Branch:** `main` (single commit: `9d1dac5`)

## What Exists

### Implemented Modules (all complete)
```
lawtime/
├── tracker.py     # Window capture, idle detection, event merging (generator-based)
├── database.py    # SQLite CRUD with indices
├── config.py      # JSON settings in %LOCALAPPDATA%\TimeLogger
├── exporter.py    # JSON export with LLM-optimized format
├── tray.py        # System tray (green=tracking, yellow=paused)
└── __main__.py    # App coordinator, threading model
```

### Key Documentation
- `ai_docs/LawTime_Tracker_PRD.md` - Complete requirements, data model, config defaults
- `ai_docs/Progress/SESSION2_SUMMARY.md` - Implementation details, architecture patterns
- `QUICKSTART.md` - 5-minute setup guide
- `CLAUDE.md` - Project-specific instructions

### Red Herrings (skip these)
- `ai_docs/compass_artifact_*.md` - Commercial tool comparisons, not relevant
- `GITHUB_SETUP.md`, `init-git.bat`, `init-git.sh` - Obsolete, git already initialized

## What's Next

### Immediate: Windows Testing
```powershell
cd C:\Users\Brahm\Git\TimeLogger
venv\Scripts\activate
python -m lawtime.tracker    # 30-second smoke test
python -m lawtime            # Full app with system tray
```

### Validation Needed
- [ ] Overnight stability (8+ hours)
- [ ] Memory <50MB, CPU <1%
- [ ] Export JSON → feed to Claude for categorization accuracy

## Technical Context

### Environment
- **Development:** WSL2 Ubuntu 24.04 with Claude Code CLI
- **Testing:** Windows 11 PowerShell (required for pywin32 APIs)
- **Git:** Use `git.exe` from WSL (not `git`) to avoid NTFS permission errors

### WSL/Windows Gotchas
- `git init` fails in WSL on `/mnt/c/` paths → use `git.exe` instead
- Python venv creation fails on NTFS from WSL → create venv in Windows PowerShell
- Symlink exists: `~/timelogger` → `/mnt/c/Users/Brahm/Git/TimeLogger`

### Windows APIs Used
```python
# Window capture
hwnd = win32gui.GetForegroundWindow()
title = win32gui.GetWindowText(hwnd)
_, pid = win32process.GetWindowThreadProcessId(hwnd)
app = psutil.Process(pid).name()

# Idle detection
windll.user32.GetLastInputInfo()  # via ctypes LASTINPUTINFO struct
```

### Known Limitations (expected, documented in PRD)
- Outlook reading pane shows "Inbox" not email subjects (use Legacy Outlook or double-click)
- URL extraction not implemented (window titles only)
- Some admin-level windows won't report titles to non-admin process

## Failed Approaches
- **ActivityWatch fork:** Rejected - requires REST server, unnecessary complexity for our needs
- **pywin32_postinstall:** Shows "No module named pywin32_postinstall" but window capture works anyway - ignore this error

## Config Defaults
| Setting | Value | Notes |
|---------|-------|-------|
| poll_interval_seconds | 1.0 | Balance granularity vs CPU |
| idle_threshold_seconds | 180 | 3 minutes before marking idle |
| merge_threshold_seconds | 2.0 | Brief switches merged |
| start_tracking_on_launch | true | Auto-start |

## File Locations (runtime)
```
%LOCALAPPDATA%\TimeLogger\
├── lawtime.db      # Activity database (NEVER commit)
└── config.json     # User settings
```

## User Context
- Civil litigation lawyer, Vancouver BC
- Python hobbyist level
- Uses: Outlook, Chrome, Word, CanLII, court websites
- Goal: Automatic time capture → JSON export → LLM categorization → billing
