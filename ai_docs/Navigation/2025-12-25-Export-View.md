# Export View

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Export View allows exporting tracked activity data for LLM processing or import into billing software.

---

## Menu Access

- **View → Export** (F7)
- **File → Export → Export Activities...** - Opens this view directly

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  EXPORT DATA                                                                │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ┌─ Date Range ──────────────────────────────────────────────────────────┐  │
│  │ From: [Dec 1, 2024  📅]     To: [Dec 22, 2024  📅]                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Filter ──────────────────────────────────────────────────────────────┐  │
│  │ ● All matters                                                         │  │
│  │ ○ By Client: [Select client ▼]                                        │  │
│  │ ○ By Matter: [Select matter ▼]                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Status ──────────────────────────────────────────────────────────────┐  │
│  │ ☑ Uncategorized    ☑ WIP    ☑ Billed    ☑ Non-Billable               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Format ──────────────────────────────────────────────────────────────┐  │
│  │ ● JSON (for LLM processing)                                           │  │
│  │ ○ CSV (spreadsheet import)                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Preview ─────────────────────────────────────────────────────────────┐  │
│  │ 147 activities • WIP: 20.5h • Billed: 12.0h • Non-Billable: 8.0h      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                              [Cancel]  [📤 Export...]       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Date Range Section

| Field | Description |
|-------|-------------|
| From | Start date for export range |
| To | End date for export range |
| 📅 | Opens calendar date picker |

---

## Filter Section

| Option | Description |
|--------|-------------|
| All matters | Export all tracked activities |
| By Client | Filter to activities for a specific client |
| By Matter | Filter to activities for a specific matter |

When "By Client" is selected, the dropdown shows clients imported from the user's folder structure. When "By Matter" is selected, the dropdown shows all matters (optionally filtered by client first).

---

## Status Section

Checkboxes to include/exclude activities by billing status:

| Status | Description |
|--------|-------------|
| Uncategorized | Activities not yet categorized by AI |
| WIP | Work in progress (categorized, not yet billed) |
| Billed | Already invoiced to client |
| Non-Billable | Administrative, personal, or non-billable work |

All statuses are checked by default.

---

## Format Section

| Format | Description | Use Case |
|--------|-------------|----------|
| JSON | Structured data format | LLM processing, AI categorization |
| CSV | Comma-separated values | Spreadsheet import, billing software |

---

## Preview Section

Shows summary of what will be exported:

- Number of activities
- Hours breakdown by status (WIP / Billed / Non-Billable)

Preview updates automatically when filters change.

---

## Actions

| Button | Action |
|--------|--------|
| Cancel | Close without exporting |
| Export... | Opens save file dialog |

---

## Quick Export Options

Available via File menu without opening Export View:

| Menu Item | Action |
|-----------|--------|
| File → Export → Quick Export (JSON) | Export current view to JSON |
| File → Export → Quick Export (CSV) | Export current view to CSV |

Quick exports use:
- Current date filter from header
- All items in current view
- All statuses included

---

## Export Formats Detail

### JSON Format

```json
{
  "export_date": "2024-12-22T10:30:00",
  "date_range": {
    "from": "2024-12-01",
    "to": "2024-12-22"
  },
  "summary": {
    "total_activities": 147,
    "wip_hours": 20.5,
    "billed_hours": 12.0,
    "non_billable_hours": 8.0,
    "matters_count": 3
  },
  "activities": [
    {
      "id": "abc123",
      "start_time": "2024-12-01T08:02:00",
      "end_time": "2024-12-01T09:25:00",
      "duration_minutes": 83,
      "application": "Microsoft Word",
      "title": "Contract_Draft_v3.docx",
      "matter": "Smith v. Jones",
      "client": "Johnson & Associates",
      "status": "wip"
    }
  ]
}
```

### CSV Format

```csv
Date,Start Time,End Time,Duration,Application,Title,Matter,Client,Status
2024-12-01,08:02,09:25,1:23,Microsoft Word,Contract_Draft_v3.docx,Smith v. Jones,Johnson & Associates,wip
```

---

## Related

- [Activities View](2025-12-25-Activities-View.md) - Review activities before export
