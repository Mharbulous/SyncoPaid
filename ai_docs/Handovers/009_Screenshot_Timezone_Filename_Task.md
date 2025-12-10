# Screenshot Filename Timezone Fix - Handover

## Task
Change screenshot filenames from UTC-based `HHMMSS_appname.jpg` to local-time with timezone: `YYYY-MM-DD_HH-MM-SS_PST_appname.jpg`

## Current State
✅ Screenshot capture is **working** (issue was missing `imagehash` dependency)
✅ All dependencies installed: pywin32, psutil, PIL, imagehash
✅ Config: `screenshot_enabled: true`, interval: 10s
⚠️ Problem: Filenames use UTC time, confusing for local user

## The Issue
Current filename format (screenshot.py:375-401):
```python
time_str = dt.strftime('%H%M%S')  # UTC time
filename = f"{time_str}_{app_name}.jpg"
# Result: 072505_WindowsTerminal.jpg (7:25 AM UTC)
```

User works in Pacific (UTC-8). Late night work (after 4 PM PST / midnight UTC) creates files in "next day" folders with confusing timestamps.

**Requested format:** `2025-12-09_23-25-05_PST_WindowsTerminal.jpg`

## Key Files to Modify

### 1. `lawtime/tracker.py:344`
Currently generates UTC timestamp for screenshot submission:
```python
timestamp = datetime.now(timezone.utc).isoformat()
```

**Change to local time with timezone awareness:**
```python
timestamp = datetime.now().astimezone().isoformat()
```

This preserves timezone info in ISO format (e.g., `2025-12-09T23:25:05-08:00`).

### 2. `lawtime/screenshot.py:375-401` (`_get_screenshot_path`)
Currently:
- Extracts time as `%H%M%S`
- Directory: `YYYY-MM-DD` (UTC date)
- Filename: `HHMMSS_appname.jpg`

**Modify to:**
- Extract timezone abbreviation (PST, PDT, EST, etc.)
- Directory: `YYYY-MM-DD` (local date)
- Filename: `YYYY-MM-DD_HH-MM-SS_{TZ}_appname.jpg`

**Getting timezone abbreviation:**
```python
dt = datetime.fromisoformat(timestamp)  # Now has timezone info
tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", etc.
```

Note: `%Z` returns abbreviation (PST/PDT) which auto-adjusts for DST. Use `%z` for offset (`-0800`) if preferred.

### 3. `lawtime/database.py:357-386` (`insert_screenshot`)
Database stores `captured_at` timestamp. Should still use ISO format with timezone (no changes needed, but verify compatibility).

## Red Herrings (Skip These)

- **`test_screenshot_direct.py`** - Diagnostic tool, not production code
- **`diagnose_screenshots.py`** - Diagnostic tool, not production code
- **`lawtime/exporter.py`** - JSON export, unrelated to screenshot filenames
- **`lawtime/tray.py`** - System tray UI only
- **ActivityEvent timestamps** (tracker.py:312) - These should **stay UTC** for database consistency; only screenshot filenames need local time

## Previous Approaches & Why They Failed

**Session 1-2:** Screenshot capture not working
- **Tried:** Adding diagnostic logging, checking config
- **Failed because:** Missing `imagehash` dependency caused `WINDOWS_APIS_AVAILABLE = False`
- **Fixed by:** `pip install -r requirements.txt`

**Redundant API check issue:**
- tracker.py had `if self.screenshot_worker and WINDOWS_APIS_AVAILABLE` check
- screenshot.py also checked `WINDOWS_APIS_AVAILABLE` internally
- **Fixed by:** Removing redundant check in tracker.py:228, letting worker handle it

## Environment Gotchas & Debug History

### Critical Dependency Issue
**Problem:** Screenshots silently failed despite config showing `screenshot_enabled: true`

**Root cause:** `imagehash` package not installed
- `requirements.txt` includes it, but wasn't installed initially
- Without imagehash, PIL import succeeds but `PIL_AVAILABLE = False` in screenshot.py
- This cascades to `WINDOWS_APIS_AVAILABLE = False` in screenshot.py
- Result: `_capture_window()` returns None, no screenshots saved

**Diagnostic process:**
1. Created `diagnose_screenshots.py` tool that revealed:
   - ✓ PIL/Pillow installed
   - ✗ imagehash missing
   - WINDOWS_APIS_AVAILABLE: False
2. Fixed by: `pip install -r requirements.txt` (installs imagehash + numpy, scipy, PyWavelets)

### Two WINDOWS_APIS_AVAILABLE Variables (Confusing!)
**tracker.py:28** checks: `win32gui`, `win32process`, `psutil`
**screenshot.py:41** checks: `win32gui`, `PIL.ImageGrab`, AND `PIL_AVAILABLE` (which requires imagehash)

These are DIFFERENT variables in different scopes. If tracker.py's check passes but screenshot.py's fails, screenshots won't work. The fix removed redundant check from tracker loop, letting worker handle it internally.

### Environment Setup Issues

**Git Bash on Windows (MINGW64):**
- User runs commands via Git Bash, not PowerShell
- Path separators: Use `/` not `\` (e.g., `venv/Scripts/activate`)
- Activate venv: `source venv/Scripts/activate` (not `venv\Scripts\activate.ps1`)
- After activation, prompt shows `(venv)`

**Wrong directory errors:**
```bash
# ✗ WRONG - No module named lawtime
python -m lawtime

# ✓ CORRECT - Must be in project directory
cd C:/Users/Brahm/Git/TimeLogger
source venv/Scripts/activate
python -m lawtime
```

**PowerShell alternative:**
If using PowerShell instead of Git Bash:
```powershell
cd C:\Users\Brahm\Git\TimeLogger
venv\Scripts\Activate.ps1  # Use backslashes
python -m lawtime
```

### Dependency Installation Order Matters
```bash
# Must activate venv FIRST
source venv/Scripts/activate
pip install -r requirements.txt

# If imagehash is missing, diagnostic shows:
# ✗ Missing dependency: imagehash (or numpy, scipy)
```

### Python Version & Platform
- **Python 3.13** (latest version, some syntax differences from 3.11)
- **Windows 11** target platform
- **Claude Code Web runs Linux** - can't test Windows APIs, must test on user's machine
- User data path: `C:\Users\Brahm\AppData\Local\TimeLogger\`

### Testing Screenshot Capture
After fixing imagehash, logs showed success:
```
Screenshot capture enabled: interval=10.0s, tracker_apis_available=True
Screenshot submitted #1 for WindowsTerminal.exe
Screenshot captured #1 (1129x635)
Saved new screenshot: C:\Users\Brahm\...\2025-12-10\072505_WindowsTerminal.jpg
```

If you DON'T see these logs, run `python diagnose_screenshots.py` to identify missing dependencies.

## Technical Context

### Timezone Handling in Python
```python
# UTC (current approach)
datetime.now(timezone.utc)  # 2025-12-10 07:25:05+00:00

# Local with timezone (needed)
datetime.now().astimezone()  # 2025-12-09 23:25:05-08:00

# Extract timezone abbreviation
dt.strftime('%Z')  # "PST" or "PDT" (auto DST)
dt.strftime('%z')  # "-0800" (numeric offset)
```

**Important:** Use `datetime.astimezone()` not `datetime.now()` alone (naive datetime has no TZ info).

### Filename Sanitization
Already implemented (screenshot.py:397-398):
```python
app_name = app_name.replace('.exe', '').replace('.', '_')[:20]
```

## Useful Resources

- **Python timezone handling:** https://docs.python.org/3/library/datetime.html#datetime.datetime.astimezone
- **strftime codes:** https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
  - `%Z` = timezone name (PST, EST, etc.)
  - `%z` = UTC offset (-0800, +0530, etc.)
- **Why use astimezone():** https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime

## Testing After Changes

1. **Stop running app** (Ctrl+C in terminal)
2. **Delete test screenshots:** `%LOCALAPPDATA%\TimeLogger\screenshots\`
3. **Run app:** `python -m lawtime`
4. **Verify new filename format** matches `YYYY-MM-DD_HH-MM-SS_PST_appname.jpg`
5. **Check directory name** is local date, not UTC date
6. **Test overnight** (before/after midnight local) to verify date boundaries

## Current Branch
`claude/add-screen-capture-01F3Kn6rMAZREVZjw6mi83uZ`

User plans to continue in new session, then merge to main once working.

## Environment
- Windows 11, Python 3.13, Pacific timezone (Vancouver)
- Project: `C:\Users\Brahm\Git\TimeLogger`
- Data: `%LOCALAPPDATA%\TimeLogger\`
- venv must be activated: `source venv/Scripts/activate` (Git Bash)
