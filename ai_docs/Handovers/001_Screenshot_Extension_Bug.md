# 001 - Screenshot Extension Missing Bug

## Issue
Screenshots saved without `.jpg` extension despite code explicitly including it.

**Observed**: `2025-12-09-23-57-53-UTC-08` (no extension, no app name)
**Expected**: `2025-12-09_23-57-53_UTC-08.jpg` (user's preferred format)

## Current State (Commit cd78bf5)

✅ Timezone changes committed to `claude/continue-work-01J9HBgUVaTRphZancrAn32D`

**Changes made:**
- `tracker.py:357` - Changed to `datetime.now().astimezone().isoformat()` (local TZ)
- `screenshot.py:396-402` - New format: `{time_str}-{tz_abbr}_{app_name}.jpg`

**Code (screenshot.py:395-403):**
```python
time_str = dt.strftime('%Y-%m-%d-%H-%M-%S')
tz_abbr = dt.strftime('%Z')  # Gets "PST", "PDT", "EST", etc.
app_name = window_app if window_app else 'unknown'
app_name = app_name.replace('.exe', '').replace('.', '_')[:20]

filename = f"{time_str}-{tz_abbr}_{app_name}.jpg"  # .jpg IS here
return date_dir / filename
```

## The Mystery

Code clearly shows `.jpg` on line 402, yet files lack extension. Additionally:
1. `UTC-08` suggests `%Z` returning empty/unexpected value (offset showing instead)
2. No underscore + app_name visible in actual filename
3. Path object truncation? Windows filename issue?

## Investigation Plan

### 1. Check Actual Runtime Behavior
Run app with debug logging to see:
```python
logging.debug(f"tz_abbr: '{tz_abbr}'")
logging.debug(f"filename: {filename}")
logging.debug(f"file_path: {file_path}")
```

### 2. Test %Z on Windows Python 3.13
```python
from datetime import datetime
dt = datetime.now().astimezone()
print(f"%%Z = '{dt.strftime('%Z')}'")  # Might be empty on Windows
print(f"%%z = '{dt.strftime('%z')}'")  # Offset like -0800
```

**Known issue**: Python `%Z` can return empty string on Windows depending on locale settings.
**Source**: https://bugs.python.org/issue38744

### 3. Check PIL.Image.save() Behavior
Line 426: `img.save(str(file_path), 'JPEG', quality=self.quality, optimize=True)`

PIL might:
- Ignore extension if format specified explicitly?
- Have Windows-specific path handling issues?
- Check PIL version: `pip show Pillow`

### 4. Verify Path Object Stringification
```python
# Test if Path is mangling filename
test_path = Path("test/2025-12-09-23-57-53-PST_app.jpg")
print(f"Path: {test_path}")
print(f"str(): {str(test_path)}")
print(f"name: {test_path.name}")
```

## Likely Root Causes (Ranked)

1. **%Z returns empty on Windows** - Format becomes `2025-12-09-23-57-53-_app.jpg`, then something strips rest?
2. **PIL.Image.save() ignores extension** when format explicitly given as 'JPEG'
3. **Windows path/filename restrictions** - Special chars in tz_abbr causing truncation
4. **File already exists** logic overwriting with wrong name

## Key Files

### Primary (Modify These)
- `lawtime/screenshot.py:375-403` - `_get_screenshot_path()` method
- `lawtime/screenshot.py:422-448` - `_save_new_screenshot()` method
- `lawtime/tracker.py:357` - Timestamp generation

### Secondary (Read Only)
- `lawtime/database.py:357-386` - `insert_screenshot()` (stores path as-is)

## Red Herrings (Skip These)
- `test_screenshot_direct.py` - Diagnostic only
- `diagnose_screenshots.py` - Diagnostic only
- `lawtime/exporter.py` - JSON export, unrelated
- `_overwrite_screenshot()` method - Uses existing path from metadata

## Recommended Fix (User Preferred Format)

**Target format**: `2025-12-09_23-57-53_UTC-08.jpg`

Benefits:
- Underscores separate major components (easier to read)
- Uses `%z` offset (more reliable than `%Z` on Windows)
- No app name (simpler, less variable)
- Clearer visual parsing

**Implementation** (screenshot.py:395-403):
```python
# Generate filename: YYYY-MM-DD_HH-MM-SS_UTC±HH.jpg
date_str = dt.strftime('%Y-%m-%d')
time_str = dt.strftime('%H-%M-%S')
tz_offset = dt.strftime('%z')  # -0800, +0530, etc.
# Format offset as UTC-08 instead of -0800
tz_str = f"UTC{tz_offset[:3]}"  # UTC-08, UTC+05, etc.

filename = f"{date_str}_{time_str}_{tz_str}.jpg"
# Result: 2025-12-09_23-57-53_UTC-08.jpg
return date_dir / filename
```

## Alternative Options (If App Name Needed)

### Option A: Append App Name
```python
filename = f"{date_str}_{time_str}_{tz_str}_{app_name}.jpg"
# Result: 2025-12-09_23-57-53_UTC-08_WindowsTerminal.jpg
```

### Option B: Fallback for Empty %Z (Original Approach)
```python
tz_abbr = dt.strftime('%Z') or dt.strftime('%z')
# Less reliable on Windows
```

## Testing Protocol

1. **Stop app**: Ctrl+C existing process
2. **Clear test data**: Delete `%LOCALAPPDATA%\TimeLogger\screenshots\`
3. **Add debug logging** to screenshot.py before testing
4. **Run**: `python -m lawtime` (15+ seconds for first screenshot)
5. **Check**:
   - Actual files on disk (extension present?)
   - Console output (logging shows what?)
   - Database `screenshots` table `file_path` column

## Environment Context

- **Windows 11**, Python 3.13, Pacific timezone (Vancouver BC, UTC-8)
- **Git Bash** terminal (not PowerShell)
- **venv activation**: `source venv/Scripts/activate`
- **Project**: `C:\Users\Brahm\Git\TimeLogger`
- **Data**: `%LOCALAPPDATA%\TimeLogger\`
- **Branch**: `claude/continue-work-01J9HBgUVaTRphZancrAn32D`

## Python strftime References

- **%Z behavior**: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
  - Returns timezone name (PST, EST) **if available**
  - Can return **empty string** on Windows ([Python bug #38744](https://bugs.python.org/issue38744))
  - Platform-dependent behavior
- **%z**: Always returns offset like `-0800`, `+0530` (more reliable)
- **Windows timezone**: https://stackoverflow.com/questions/2134619/getting-local-time-zone-name-in-python

## Success Criteria

Screenshots should be saved as:
- **Format**: `YYYY-MM-DD_HH-MM-SS_UTC±HH.jpg`
- **Example**: `2025-12-09_23-57-53_UTC-08.jpg`
- **Extension**: `.jpg` must be present
- **Directory**: Local date `YYYY-MM-DD/` (not UTC)
- **TZ**: Numeric offset formatted as `UTC-08`, `UTC+05`, etc.
- **Separators**: Underscores between major components, hyphens within
