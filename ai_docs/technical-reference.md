# SyncoPaid Technical Reference

This document contains detailed technical reference material for SyncoPaid. For essential project context and commands, see the main `CLAUDE.md`.

## Configuration Defaults

Settings stored in `%LOCALAPPDATA%\SyncoPaid\config.json`:

| Setting | Default | Purpose |
|---------|---------|---------|
| poll_interval_seconds | 1.0 | Window check frequency |
| idle_threshold_seconds | 180 | Seconds before marking idle |
| merge_threshold_seconds | 2.0 | Gap to merge identical events |
| start_tracking_on_launch | true | Auto-start tracking |
| screenshot_enabled | true | Enable periodic screenshot capture |
| screenshot_interval_seconds | 10 | Seconds between screenshot attempts |
| screenshot_quality | 65 | JPEG quality (1-100) |
| screenshot_max_dimension | 1920 | Max width/height in pixels |
| screenshot_threshold_identical | 0.92 | Similarity >= this overwrites previous |
| screenshot_threshold_significant | 0.70 | Similarity < this saves new screenshot |

## Key Classes

### ActivityEvent (tracker.py)
Dataclass with fields: `timestamp`, `duration_seconds`, `app`, `title`, `url`, `is_idle`

### TrackerLoop (tracker.py)
Generator-based tracking loop with event merging logic. `start()` yields `ActivityEvent` instances on state changes.

### ScreenshotWorker (screenshot.py)
Async screenshot capture with perceptual hashing (dHash) for deduplication. Non-blocking operation.

### Database (database.py)
SQLite wrapper with methods: `insert_event()`, `insert_screenshot()`, `query_events()`, `get_statistics()`

### ConfigManager (config.py)
Manages settings with defaults and JSON persistence. Auto-creates config on first run.

### TrayIcon (tray.py)
pystray-based system tray with callbacks: start, pause, export, quit.

## Windows APIs Used

| API | Purpose |
|-----|---------|
| `win32gui.GetForegroundWindow()` | Get active window handle |
| `win32gui.GetWindowText()` | Get window title from handle |
| `win32process.GetWindowThreadProcessId()` | Get process ID from window |
| `psutil.Process(pid).name()` | Get executable name from PID |
| `windll.user32.GetLastInputInfo()` | Detect idle time (keyboard/mouse) |
| `PIL.ImageGrab.grab()` | Capture screenshot of window region |
| `win32gui.GetWindowRect()` | Get window position/dimensions |

## Data Flow Details

1. **TrackerLoop.start()** - Generator that polls `get_active_window()` and `get_idle_seconds()` every 1 second
2. **Screenshot Request** - Every 10 seconds (configurable), tracker submits async request to `ScreenshotWorker`
3. **Event Yielding** - State changes yield `ActivityEvent` dataclass instances
4. **Database Insert** - `SyncoPaidApp._run_tracking_loop()` inserts events via `Database.insert_event()`
5. **Screenshot Processing** - `ScreenshotWorker` captures, deduplicates via dHash, saves to disk + database
6. **Export** - `Exporter.export_to_json()` queries database and writes structured JSON for LLM processing
