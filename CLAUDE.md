# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LawTime Tracker is a Windows 11 desktop application that automatically captures window activity for civil litigation lawyers. It runs in the background, recording window titles and application names at second-level precision. All data stays local (SQLite database) for attorney-client privilege preservation. Exported JSON is designed for processing by external LLM tools for billing categorization.

## Development Commands

```bash
# Activate virtual environment (required)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m lawtime

# Test individual modules
python -m lawtime.tracker    # Window capture test (30s)
python -m lawtime.database   # Database operations test
python -m lawtime.config     # Config management test
python -m lawtime.exporter   # Export functionality test
python -m lawtime.tray       # System tray test

# Quick API verification tests
python test_window.py        # Test pywin32 window capture
python test_idle.py          # Test idle detection API
python test_tray.py          # Test pystray system tray
```

## Architecture

### Module Structure

```
lawtime/
├── __main__.py    # Entry point, LawTimeApp coordinator class
├── tracker.py     # TrackerLoop: polls active window, detects idle, yields ActivityEvent
├── database.py    # SQLite operations (insert, query, delete, statistics)
├── exporter.py    # JSON export with date filtering
├── config.py      # ConfigManager: loads/saves %LOCALAPPDATA%\TimeLogger\config.json
└── tray.py        # TrayIcon: pystray-based system tray with menu
```

### Data Flow

1. `TrackerLoop.start()` is a generator that polls `get_active_window()` and `get_idle_seconds()` every 1 second
2. State changes yield `ActivityEvent` dataclass instances
3. `LawTimeApp._run_tracking_loop()` inserts events into SQLite via `Database.insert_event()`
4. `Exporter.export_to_json()` queries database and writes structured JSON for LLM processing

### Key Classes

- **ActivityEvent** (tracker.py): Dataclass with timestamp, duration_seconds, app, title, url, is_idle
- **TrackerLoop** (tracker.py): Generator-based tracking loop with event merging logic
- **Database** (database.py): SQLite wrapper with insert_event(), query_events(), delete_events()
- **ConfigManager** (config.py): Settings management with defaults and JSON persistence
- **TrayIcon** (tray.py): System tray with start/pause/export/quit callbacks

### Windows APIs Used

- `win32gui.GetForegroundWindow()` / `GetWindowText()` - Active window title
- `win32process.GetWindowThreadProcessId()` - Process ID from window handle
- `psutil.Process(pid).name()` - Executable name from PID
- `windll.user32.GetLastInputInfo()` - Idle time detection (keyboard/mouse inactivity)

## File Locations

- **Database**: `%LOCALAPPDATA%\TimeLogger\lawtime.db`
- **Config**: `%LOCALAPPDATA%\TimeLogger\config.json`
- **PRD/Docs**: `ai_docs/` directory

## Technology Stack

- Python 3.11+ (target Windows 11)
- pywin32: Windows API access
- psutil: Process information
- pystray + Pillow: System tray icon
- tkinter: Native file dialogs (stdlib)
- SQLite: Local database (stdlib)

## Configuration Defaults

| Setting | Default | Purpose |
|---------|---------|---------|
| poll_interval_seconds | 1.0 | Window check frequency |
| idle_threshold_seconds | 180 | Seconds before marking idle |
| merge_threshold_seconds | 2.0 | Gap to merge identical events |
| start_tracking_on_launch | true | Auto-start tracking |

## Known Limitations

- URL extraction not implemented (captures window titles only)
- New Outlook doesn't expose email subjects (use Legacy Outlook)
- Outlook reading pane shows generic "Inbox" instead of email subjects
