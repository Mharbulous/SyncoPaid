# CLAUDE.md

## Critical Rules

- **IMPORTANT**: Do not build fallbacks to avoid problematic code; it only hides code rot.
- **ALWAYS**: Identify root causes before attempting to fix or avoid problems.
- **NEVER** modify SQLite database directly

## Terminology

**Use these terms consistently to prevent feature creep:**

| Internal (Code/Docs) | User-Facing (UI) | Definition |
|----------------------|------------------|------------|
| **Bucket** | **Matter** | A category for billable time, imported from the user's folder structure. We do NOT create, edit, or manage buckets — we import folder paths and use them as labels. |
| **Activity** | **Activity** | A tracked window/application event with start time, duration, and context. |
| **Review** | **Review** | The user workflow: accept or reject AI suggestions. NOT "manage" or "organize." |

**When to use which term:**

| Context | Use | Example |
|---------|-----|---------|
| Source code (variables, classes, comments) | Bucket | `bucket_id`, `assign_to_bucket()` |
| Technical documentation | Bucket | "Activities are categorized into buckets" |
| UI mockups and wireframes | Matter | Dialog showing "Matter: Smith v. Jones" |
| User-facing labels in the app | Matter | Menu item "Filter by Matter" |
| Error messages shown to users | Matter | "No matter selected" |

**Why this matters:** Using "Matter" internally may cause AI assistants to build practice management features (create matter, edit matter, archive matter). "Bucket" reminds us these are just imported folder paths used as labels — nothing to manage.

**Avoid in code/docs:**
- "Matter" (implies practice management)
- "Project" (implies project management)
- "Case" (implies case management)
- "Assign to matter" (implies management — use "assign to bucket" or "categorize")

## Development Environments

Development occurs in **two environments**:

| Environment | OS | Virtual Env | Path Format |
|-------------|-----|-------------|-------------|
| Local IDE | Windows 11 | `venv\Scripts\activate` | Backslashes (`\`) |
| Remote Sandbox / CI | Linux | `source venv/bin/activate` | Forward slashes (`/`) |

**Detect environment:** Check for `CI=true` env var or Linux platform.

**When writing plans or scripts:** Use platform-appropriate commands, or provide both variants.

## Project Summary

**SyncoPaid** is a Windows 11 desktop app that runs in background tracking window activities. Data stored in local SQLite. Exports JSON for LLM billing categorization.

**Target Platform**: Windows 11 (deployment)
**User Data Path**: `C:\Users\Brahm\AppData\Local\SyncoPaid\`

## Commands

```bash
# Activate venv first (required)
venv\Scripts\activate

# Run application
python -m syncopaid

# Test individual modules
python -m syncopaid.tracker    # Window capture (30s)
python -m syncopaid.database   # Database ops
python -m syncopaid.config     # Config management
python -m syncopaid.exporter   # Export functionality
python -m syncopaid.tray       # System tray

# Quick API tests
python test_window.py          # pywin32 capture
python test_idle.py            # Idle detection
python test_tray.py            # pystray tray
```

## Tech Stack

Python 3.11+ | pywin32 | psutil | pystray + Pillow | imagehash | SQLite

## Architecture

```
src/syncopaid/
├── __main__.py    # Entry point, SyncoPaidApp coordinator
├── tracker.py     # TrackerLoop: polls active window, yields ActivityEvent
├── screenshot.py  # ScreenshotWorker: async capture with dHash deduplication
├── database.py    # SQLite: insert, query, delete, statistics
├── exporter.py    # JSON export with date filtering
├── config.py      # ConfigManager: %LOCALAPPDATA%\SyncoPaid\config.json
└── tray.py        # TrayIcon: pystray system tray with menu
```

**Data Flow**: TrackerLoop polls window every 1s → yields ActivityEvent on change → SyncoPaidApp inserts to SQLite → ScreenshotWorker captures every 10s with dHash dedup → Exporter outputs JSON

## File Locations

| File | Path |
|------|------|
| Database | `%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db` |
| Config | `%LOCALAPPDATA%\SyncoPaid\config.json` |
| Screenshots | `%LOCALAPPDATA%\SyncoPaid\screenshots\YYYY-MM-DD\` |
| Docs | `ai_docs/` |


## Reference

For detailed configuration defaults, Windows APIs used, and key class documentation, see `ai_docs/technical-reference.md`.

## Verification

Before completing changes:
1. Run relevant module test: `python -m syncopaid.<module>`
2. Verify no regressions in window tracking or screenshot capture
3. Test system tray functionality if UI changed
