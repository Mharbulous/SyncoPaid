# LawTime Tracker — Product Requirements Document

**Version:** 1.0 (MVP)  
**Date:** December 9, 2025  
**Status:** Draft

---

## 1. Executive Summary

LawTime Tracker is a local Windows 11 desktop application that automatically captures granular activity data for a civil litigation lawyer. The app runs silently in the background, recording window titles, application names, browser URLs, and timestamps at second-level precision. All data remains entirely local (never uploaded to any server), preserving attorney-client privilege.

The MVP focuses exclusively on **data collection and JSON export**—providing the raw activity log needed to experiment with external LLM tools for automatic matter categorization and billing narrative generation. AI integration is explicitly pending to a future version.

---

## 2. Problem Statement

### 2.1 The Reconstruction Problem

Legal time tracking is fundamentally a reconstruction problem. Studies show lawyers record only 2.9 billable hours per day on average despite working 8+ hours. The cognitive burden of remembering what you worked on—especially when switching between 5-10 client matters daily—causes massive revenue leakage:

- Waiting until end-of-day loses 10-15% of billable time
- Waiting 24+ hours increases loss to 25%
- Quick tasks (5-minute emails, brief calls) get forgotten entirely
- Manual tracking adds 20-40 minutes of non-billable overhead daily

### 2.2 Current Tool Limitations

Existing automatic time trackers (TimeCamp, Memtime, ManicTime) have key limitations for this use case:

- Limited export formats or restricted API access
- Subscription costs for features that aren't needed
- No ability to customize data capture for legal workflows
- Closed systems that don't allow experimentation with LLM categorization

---

## 3. Goals and Non-Goals

### 3.1 MVP Goals

1. **Passive background capture:** Record all foreground window activity without requiring any user interaction during work
2. **Second-level precision:** Capture timestamps accurate to the second for later aggregation into billing increments
3. **Rich metadata:** Capture application name, window title, and browser URL—the signals needed for AI categorization
4. **Idle detection:** Exclude periods of inactivity (no keyboard/mouse input) from the activity log
5. **Local-only storage:** All data stays on the user's machine—never uploaded to any external server
6. **JSON export:** Export activity data in structured JSON format for processing by external LLM tools
7. **Minimal UI:** System tray icon with basic controls (start/stop, export, quit)—no complex interface

### 3.2 Explicit Non-Goals (MVP)

1. **AI/LLM integration:** No automatic categorization or billing narrative generation—this is Phase 2
2. **Practice management integration:** No Clio, PracticePanther, or other software sync
3. **Timeline visualization:** No graphical timeline or calendar view (export raw data instead)
4. **Multi-device sync:** Single-machine only, no cloud synchronization
5. **Keystroke logging:** No capture of actual typed content—only window metadata
6. **Screenshot capture:** No visual recording of screen content

---

## 4. User Stories

### 4.1 Core Workflow

- **As a lawyer,** I want the tracker to start automatically when Windows boots, so I never forget to enable tracking
- **As a lawyer,** I want tracking to happen silently in the background, so it doesn't interrupt my work
- **As a lawyer,** I want to see a system tray icon confirming tracking is active, so I have peace of mind
- **As a lawyer,** I want to export a day's activities with two clicks, so I can process them with an LLM tool

### 4.2 Data Quality

- **As a lawyer,** I want the tracker to capture which document I'm working on (from the window title), so I can match time to specific files
- **As a lawyer,** I want browser URLs captured when I'm doing legal research, so I know which matters involved Westlaw/CanLII time
- **As a lawyer,** I want idle time excluded automatically, so lunch breaks don't inflate my activity log
- **As a lawyer,** I want timestamps accurate to the second, so I can calculate precise durations later

### 4.3 Privacy & Control

- **As a lawyer,** I want all data stored locally on my machine, so attorney-client privilege is preserved
- **As a lawyer,** I want the ability to pause tracking temporarily, so I can handle personal tasks without logging them
- **As a lawyer,** I want to delete specific time ranges from the database, so I can remove accidentally captured personal activity

---

## 5. Functional Requirements

### 5.1 Activity Capture

| ID | Requirement | Description |
|----|-------------|-------------|
| F-001 | Window Tracking | Capture foreground window title every 1-2 seconds when not idle |
| F-002 | Process Detection | Record executable name (e.g., WINWORD.EXE, chrome.exe, OUTLOOK.EXE) |
| F-003 | URL Capture | Extract URL from browser window titles or accessibility APIs for Chrome/Edge/Firefox |
| F-004 | Timestamp Precision | Record start time in ISO8601 format with second precision |
| F-005 | Idle Detection | Mark activity as idle when no keyboard/mouse input for configurable threshold (default: 180 seconds) |
| F-006 | Activity Merging | Combine consecutive identical window states into single events with cumulative duration |

### 5.2 Data Storage

| ID | Requirement | Description |
|----|-------------|-------------|
| F-007 | Local Database | Store all events in local SQLite database in user's AppData folder |
| F-008 | No Network | Application must never transmit data over network—completely offline operation |
| F-009 | Data Retention | Retain data indefinitely until user explicitly deletes (no auto-purge) |
| F-010 | Delete Range | Allow deletion of events within specified date/time range |

### 5.3 Export

| ID | Requirement | Description |
|----|-------------|-------------|
| F-011 | JSON Export | Export events as JSON array with all captured fields |
| F-012 | Date Filtering | Export supports start_date and end_date parameters |
| F-013 | Export Location | User selects output file path via standard Windows file dialog |

### 5.4 User Interface

| ID | Requirement | Description |
|----|-------------|-------------|
| F-014 | System Tray | Display icon in Windows system tray with status indicator (green=tracking, yellow=paused) |
| F-015 | Tray Menu | Right-click menu: Start/Pause Tracking, Export Data, Settings, Quit |
| F-016 | Startup Option | Setting to launch automatically on Windows startup (disabled by default) |
| F-017 | Export Dialog | Simple dialog to select date range and output file location |

---

## 6. Data Model

### 6.1 Event Schema

Each captured activity is stored as an event with the following structure:

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| timestamp | TEXT | ISO8601 datetime when event started (e.g., "2025-12-09T10:30:45") |
| duration_seconds | REAL | Duration of this activity in seconds (floating point for sub-second precision) |
| app | TEXT | Executable name (e.g., "WINWORD.EXE", "chrome.exe") |
| title | TEXT | Window title text (e.g., "Smith-Contract-v2.docx - Word") |
| url | TEXT | Browser URL if applicable, NULL otherwise |
| is_idle | INTEGER | Boolean (0/1) indicating if user was idle during this period |

### 6.2 SQLite Schema

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

CREATE INDEX idx_timestamp ON events(timestamp);
CREATE INDEX idx_app ON events(app);
```

### 6.3 JSON Export Format

Exported JSON follows this structure for LLM processing:

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
    },
    {
      "timestamp": "2025-12-09T09:17:47",
      "duration_seconds": 485.0,
      "app": "chrome.exe",
      "title": "Smith v. Jones - Case Analysis | Westlaw - Google Chrome",
      "url": "https://westlaw.com/Document/I1234567890",
      "is_idle": false
    }
  ]
}
```

---

## 7. Technical Architecture

### 7.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Optimized for Claude Code vibe coding; excellent Windows API bindings |
| Window API | pywin32 (win32gui, win32process) | Mature Windows API access for window titles and process info |
| Process Info | psutil | Cross-platform process name resolution |
| Idle Detection | ctypes + Windows GetLastInputInfo API | Native Windows idle detection |
| Database | SQLite (Python stdlib) | Zero configuration, single-file database |
| System Tray UI | pystray + Pillow | Simple system tray with icon generation |
| File Dialogs | tkinter (Python stdlib) | Native Windows file dialogs without extra dependencies |

### 7.2 Module Structure

```
lawtime/
├── __main__.py      # Entry point, launches system tray
├── tracker.py       # Core tracking loop (window, idle detection)
├── database.py      # SQLite operations (insert, query, delete)
├── exporter.py      # JSON export logic
├── tray.py          # System tray icon and menu
├── config.py        # Settings (idle threshold, poll interval)
└── utils.py         # URL extraction, window title parsing
```

### 7.3 Core Dependencies

```
pywin32>=306
psutil>=5.9.0
pystray>=0.19.0
Pillow>=10.0.0
```

### 7.4 Open Source Reference

**Recommended reference:** ActivityWatch (github.com/ActivityWatch/activitywatch)

Its Python-based architecture provides battle-tested patterns for window tracking, idle detection, and event storage. Key components to study:

- **aw-watcher-window:** Window title capture implementation
- **aw-watcher-afk:** Idle/AFK detection logic  
- **aw-core:** Event model and SQLite datastore
- **License:** MPL-2.0 (permits forking for personal use)

---

## 8. Configuration Options

Settings stored in `%LOCALAPPDATA%\LawTime\config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| poll_interval_seconds | 1.0 | How often to check the active window |
| idle_threshold_seconds | 180 | Seconds of no input before marking as idle |
| merge_threshold_seconds | 2.0 | Combine events if same window within this gap |
| database_path | %LOCALAPPDATA%\LawTime\lawtime.db | SQLite database location |
| start_on_boot | false | Launch automatically on Windows startup |
| start_tracking_on_launch | true | Begin tracking immediately when app starts |

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

---

## 9. Key Implementation Details

### 9.1 Window Title Capture (Windows API)

```python
import win32gui
import win32process
import psutil

def get_active_window():
    """Get foreground window info."""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process = psutil.Process(pid).name()
    except psutil.NoSuchProcess:
        process = None
    return {"title": title, "app": process, "pid": pid}
```

### 9.2 Idle Detection (Windows API)

```python
from ctypes import Structure, windll, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]

def get_idle_seconds():
    """Get seconds since last user input."""
    info = LASTINPUTINFO()
    info.cbSize = sizeof(info)
    windll.user32.GetLastInputInfo(byref(info))
    millis = windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0
```

### 9.3 Browser URL Extraction

For Chromium-based browsers (Chrome, Edge), URLs can often be extracted from window titles or via UI Automation. Fallback approach:

```python
def extract_url_from_title(title, app):
    """Extract URL hints from browser window titles."""
    # Many sites include domain in title
    # e.g., "Smith v. Jones | Westlaw - Google Chrome"
    # Full URL requires UI Automation or browser extension
    return None  # MVP: capture title only, URL extraction is enhancement
```

---

## 10. Future Phases (Post-MVP)

### 10.1 Phase 2: LLM Integration

After validating the data collection MVP and experimenting with external LLM tools:

- Local matter/client database for matching
- LLM API integration (Claude, GPT) for activity classification
- Automatic billing narrative generation
- Configurable billing increment rounding (6-minute standard)
- Review UI for approving AI-generated entries

### 10.2 Phase 3: Practice Management Integration

- Clio API integration for direct time entry submission
- LEDES format export for e-billing compliance
- Calendar integration for meeting correlation

---

## 11. Success Criteria

The MVP is considered successful when:

1. **Reliable capture:** Tracker runs continuously for 8+ hour workdays without crashes or missed events
2. **Data quality:** Window titles captured accurately enough to identify client/matter from typical naming conventions
3. **Idle accuracy:** Lunch breaks and extended away periods correctly excluded from active time
4. **Export usability:** JSON exports can be successfully processed by Claude/GPT for categorization experiments
5. **Minimal footprint:** CPU usage under 1%, memory under 50MB during normal operation

---

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Window title doesn't contain useful metadata | LLM cannot categorize activities | Adopt file naming conventions; consider Outlook email subject extraction |
| New Outlook hides email details | Cannot track individual emails | Use Legacy Outlook until Microsoft adds API support (expected late 2025) |
| Browser URL extraction fails | Research time unattributable | Fall back to window title parsing; accept browser-level granularity |
| Database grows too large | Performance degrades | Add optional archive/purge feature; export before clearing |
| pywin32 compatibility issues | App won't run | Pin to known-good version; test on target Windows 11 build |

---

## 13. Development Approach

**Vibe coding with Claude Code:** This project will be developed using Claude Code for rapid iteration. The Python codebase is chosen specifically because Claude excels at Python generation and debugging.

### Development Sequence

1. **tracker.py** — Window capture + idle detection loop (core functionality)
2. **database.py** — SQLite storage with insert/query/delete
3. **exporter.py** — JSON export with date filtering
4. **config.py** — Settings management
5. **tray.py** — System tray UI integration
6. **__main__.py** — Entry point tying it all together

### Testing Strategy

- Test each module in isolation before integration
- Run tracker overnight to verify stability
- Export sample data and feed to Claude to validate LLM readability

---

## Appendix A: Sample Window Titles

These examples represent typical window titles the tracker should capture:

```
// Microsoft Word
Smith-Contract-v2.docx - Word
12345-001_Jones_MotionToDismiss.docx - Word
Document1 - Word

// Outlook (Legacy)
RE: Smith v. Jones - Discovery Request - Outlook
Inbox - user@lawfirm.com - Outlook
Calendar - Outlook

// Outlook (New) — Limited detail
Mail - User Name - Outlook
Calendar - User Name - Outlook

// Chrome/Edge
Smith v. Jones - Case Analysis | Westlaw - Google Chrome
CanLII - 2024 BCSC 1234 - Microsoft Edge
BC Court Services Online - Google Chrome

// PDF
Smith_ExhibitA_Contract.pdf - Adobe Acrobat Reader
Jones_Affidavit_2024-12-01.pdf - Edge

// Excel
Smith_BillingStatement_2024.xlsx - Excel
```

---

## Appendix B: Sample LLM Prompt for Categorization

Once MVP is complete, this prompt template can be used with exported JSON:

```
You are a legal billing assistant. I will provide you with a JSON export of my computer activity for today. Please:

1. Group activities by likely client/matter based on window titles and filenames
2. For each group, calculate total time and round to nearest 0.1 hour (6 minutes)
3. Generate a billing narrative describing the work performed
4. Flag any activities you cannot confidently categorize

Activity data:
[paste JSON here]

My active matters:
- Smith v. Jones (Contract dispute)
- 12345-001 Johnson Estate
- XYZ Corp retainer (general corporate)
```

---

## Appendix C: File Naming Convention Recommendation

To maximize LLM categorization accuracy, adopt consistent file naming:

```
[MatterNumber]_[ClientName]_[DocType]_[Description].[ext]

Examples:
12345-001_Smith_Motion_Dismiss.docx
12345-001_Smith_Letter_OpposingCounsel_2024-12-09.docx
99999-003_Jones_Contract_ServiceAgreement_v2.docx
```

This allows the LLM to extract: matter number, client name, document type, and version info directly from window titles.
