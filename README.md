# LawTime Tracker

**Automatic time tracking for Windows 11 designed specifically for civil litigation lawyers.**

LawTime Tracker runs silently in the background, capturing your window activity at second-level precision. All data stays entirely local on your machine (never uploaded to any server), preserving attorney-client privilege. Export your activity log to JSON for processing by external LLM tools for automatic matter categorization and billing narrative generation.

## Features

- ✅ **Passive background capture** - No timers to start/stop manually
- ✅ **Second-level precision** - Accurate timestamps for precise duration calculations
- ✅ **Rich metadata** - Captures application name, window title, and idle detection
- ✅ **Local-only storage** - SQLite database stored on your machine only
- ✅ **JSON export** - Export activity data for LLM processing (Claude, GPT, etc.)
- ✅ **Minimal UI** - System tray icon with basic controls
- ✅ **Privacy-focused** - No keystroke logging, no screenshots, no cloud sync

## Requirements

- **Windows 11** (target platform)
- **Python 3.11+**
- **Dependencies**: pywin32, psutil, pystray, Pillow (see `requirements.txt`)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/timelawg.git
cd timelawg
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify installation

Test the core APIs work on your machine:

```bash
# Test window capture
python test_window.py

# Test idle detection
python test_idle.py

# Test system tray
python test_tray.py
```

If all tests pass, you're ready to run the app!

## Usage

### Run the application

```bash
python -m lawtime
```

This will:
1. Create the database at `%LOCALAPPDATA%\TimeLawg\lawtime.db`
2. Create config file at `%LOCALAPPDATA%\TimeLawg\config.json`
3. Start tracking automatically (if `start_tracking_on_launch` is true)
4. Show a system tray icon (green = tracking, yellow = paused)

### System Tray Controls

Right-click the system tray icon to access:

- **▶ Start Tracking** / **⏸ Pause Tracking** - Toggle tracking on/off
- **📤 Export Data** - Export captured activities to JSON
- **⚙ Settings** - View current configuration
- **ℹ About** - Show app information
- **❌ Quit** - Exit the application

### Export Data

1. Right-click the tray icon → **Export Data**
2. Choose a location to save the JSON file
3. The file contains all captured activities for today (default)

The exported JSON can be fed to Claude or GPT for automatic categorization:

```json
{
  "export_date": "2025-12-09T18:00:00",
  "date_range": {
    "start": "2025-12-09",
    "end": "2025-12-09"
  },
  "total_events": 342,
  "total_duration_seconds": 28847,
  "events": [
    {
      "timestamp": "2025-12-09T09:02:15",
      "duration_seconds": 932.5,
      "app": "WINWORD.EXE",
      "title": "Smith-Contract-v2.docx - Word",
      "url": null,
      "is_idle": false
    }
  ]
}
```

## Configuration

Settings are stored in `%LOCALAPPDATA%\TimeLawg\config.json`:

```json
{
  "poll_interval_seconds": 1.0,
  "idle_threshold_seconds": 180,
  "merge_threshold_seconds": 2.0,
  "database_path": null,
  "start_on_boot": false,
  "start_tracking_on_launch": true
}
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `poll_interval_seconds` | 1.0 | How often to check the active window |
| `idle_threshold_seconds` | 180 | Seconds before marking as idle (3 minutes) |
| `merge_threshold_seconds` | 2.0 | Max gap to merge identical windows |
| `database_path` | auto | Path to SQLite database |
| `start_on_boot` | false | Launch automatically on Windows startup |
| `start_tracking_on_launch` | true | Begin tracking when app starts |

Edit the config file and restart the app to apply changes.

## Database

Activity data is stored in a local SQLite database at:
```
%LOCALAPPDATA%\TimeLawg\lawtime.db
```

### Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    app TEXT,
    title TEXT,
    url TEXT,
    is_idle INTEGER DEFAULT 0
);
```

### Direct Database Access

You can query the database directly if needed:

```bash
sqlite3 "%LOCALAPPDATA%\TimeLawg\lawtime.db"
```

```sql
-- Get today's active events
SELECT timestamp, duration_seconds, app, title 
FROM events 
WHERE date(timestamp) = date('now') 
  AND is_idle = 0
ORDER BY timestamp;

-- Calculate total active time today
SELECT SUM(duration_seconds) / 3600.0 as hours
FROM events
WHERE date(timestamp) = date('now')
  AND is_idle = 0;
```

## Using with LLM Tools

### Example Claude Prompt

After exporting your activity data, you can use Claude to categorize it:

```
You are a legal billing assistant. I will provide you with a JSON export 
of my computer activity for today. Please:

1. Group activities by likely client/matter based on window titles and filenames
2. For each group, calculate total time and round to nearest 0.1 hour (6 minutes)
3. Generate a billing narrative describing the work performed
4. Flag any activities you cannot confidently categorize

Activity data:
[paste JSON here]

My active matters:
- Smith v. Jones (Contract dispute, File #12345-001)
- Johnson Estate (Probate, File #99999-003)
- XYZ Corp retainer (General corporate, File #88888-005)
```

## File Naming Convention

To maximize LLM categorization accuracy, use consistent file naming:

```
[MatterNumber]_[ClientName]_[DocType]_[Description].[ext]

Examples:
12345-001_Smith_Motion_Dismiss.docx
12345-001_Smith_Letter_OpposingCounsel_2024-12-09.docx
99999-003_Johnson_Will_Final.docx
```

This allows the LLM to extract matter number, client name, and document type directly from window titles.

## Troubleshooting

### "python" not recognized

Install Python from [python.org](https://www.python.org/downloads/) and ensure "Add to PATH" is checked during installation.

### pywin32 import errors

Run the post-install script:
```bash
python -m pywin32_postinstall -install
```

### System tray icon not visible

Windows 11 hides overflow icons by default. Click the "^" arrow in the system tray to see hidden icons. To keep it visible:
1. Right-click taskbar → Taskbar settings
2. Other system tray icons → Turn on TimeLawg

### Permission errors accessing windows

Some admin-level applications may not report window titles to non-admin processes. Run PowerShell as Administrator if needed during testing.

## Development

### Project Structure

```
timelawg/
├── lawtime/
│   ├── __init__.py      # Package initialization
│   ├── __main__.py      # Main entry point
│   ├── tracker.py       # Core tracking loop
│   ├── database.py      # SQLite operations
│   ├── exporter.py      # JSON export
│   ├── config.py        # Settings management
│   └── tray.py          # System tray UI
├── requirements.txt     # Dependencies
├── README.md           # This file
└── .gitignore          # Git exclusions
```

### Running Tests

Each module includes a `if __name__ == "__main__"` block for standalone testing:

```bash
# Test tracker
python -m lawtime.tracker

# Test database
python -m lawtime.database

# Test config
python -m lawtime.config

# Test exporter
python -m lawtime.exporter

# Test tray
python -m lawtime.tray
```

### Development Guidelines

- All code in Python 3.11+
- Use type hints for function signatures
- Follow PEP 8 style guide
- Document functions with docstrings
- Keep modules focused and single-purpose

## Known Limitations

1. **Outlook reading pane** - Shows generic "Inbox" instead of email subjects when using the preview pane. This is an architectural limitation affecting all automatic time trackers. Double-click important emails to open them in separate windows for better tracking.

2. **New Outlook** - Microsoft's redesigned Outlook doesn't expose detailed activity to third-party apps. Use Legacy Outlook for better email tracking (Help → Revert to Legacy Outlook).

3. **URL extraction** - Currently captures window titles only. Full URL extraction is a future enhancement.

## Roadmap

### Phase 1: MVP (Current)
- ✅ Window tracking
- ✅ Idle detection
- ✅ Local storage
- ✅ JSON export
- ✅ System tray UI

### Phase 2: LLM Integration (Planned)
- ⏳ Local matter/client database
- ⏳ Automatic categorization via Claude/GPT API
- ⏳ Billing narrative generation
- ⏳ Review UI for approving AI-generated entries
- ⏳ 6-minute billing increment rounding

### Phase 3: Practice Management (Future)
- ⏳ Clio integration
- ⏳ LEDES format export
- ⏳ Calendar integration
- ⏳ URL extraction for research sites

## Privacy & Security

- **Local-only**: All data stored on your machine, never uploaded anywhere
- **No keystroke logging**: Only captures window titles, not typed content
- **No screenshots**: No visual recording of screen content
- **No network access**: Application runs completely offline
- **Attorney-client privilege**: Database can be encrypted if needed

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/yourusername/timelawg
- Email: your.email@example.com

## Credits

Built with inspiration from:
- ActivityWatch (https://activitywatch.net)
- Memtime, ManicTime, Chrometa (commercial time trackers)

Developed for civil litigation lawyers who need accurate, automatic time tracking while maintaining complete data privacy.

---

**Disclaimer**: This is legal practice management software, not legal advice. The accuracy of automatic time tracking depends on consistent file naming conventions and work patterns. Always review and verify tracked time before billing clients.
