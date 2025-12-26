# Export View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Export View allows exporting tracked activity data in various formats for billing systems and other tools.

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
│  ┌─ Filters ─────────────────────────────────────────────────────────────┐  │
│  │ Client: [All ▼]    Matter: [All ▼]    Status: [All ▼]                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Format ──────────────────────────────────────────────────────────────┐  │
│  │ ● JSON (for LLM processing)                                           │  │
│  │ ○ CSV (spreadsheet)                                                   │  │
│  │ ○ PDF (billing report)                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Include ─────────────────────────────────────────────────────────────┐  │
│  │ ☑ Activity details      ☑ Billing narratives                          │  │
│  │ ☑ Time summaries        ☐ Screenshots (paths only)                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Preview ─────────────────────────────────────────────────────────────┐  │
│  │ 147 activities • 32.5 billable hours • 3 matters                      │  │
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

## Filters Section

| Filter | Options |
|--------|---------|
| Client | All clients, or select specific client |
| Matter | All matters, or select specific matter |
| Status | All, Categorized only, Uncategorized only |

---

## Format Section

| Format | Description | Use Case |
|--------|-------------|----------|
| JSON | Structured data format | LLM processing, API integration |
| CSV | Comma-separated values | Spreadsheets, billing software |
| PDF | Formatted document | Client invoices, records |

---

## Include Section

| Option | Description | Default |
|--------|-------------|---------|
| Activity details | Full activity information | ☑ |
| Billing narratives | User-entered descriptions | ☑ |
| Time summaries | Aggregated totals | ☑ |
| Screenshots (paths only) | Screenshot file paths | ☐ |

---

## Preview Section

Shows summary of what will be exported:

- Number of activities
- Total billable hours
- Number of matters included

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
- Default include options

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
    "billable_hours": 32.5,
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
      "narrative": "Drafted contract provisions..."
    }
  ]
}
```

### CSV Format

```csv
Date,Start Time,End Time,Duration,Application,Title,Matter,Client,Narrative
2024-12-01,08:02,09:25,1:23,Microsoft Word,Contract_Draft_v3.docx,Smith v. Jones,Johnson & Associates,"Drafted contract provisions..."
```

### PDF Format

Formatted report with:
- Header with date range and filters
- Summary statistics
- Activity table
- Per-matter breakdowns
- Totals

---

## Related

- [Reports View](2025-12-25-Reports-View.md) - View before exporting
- [Activities View](2025-12-25-Activities-View.md) - Review activities before export
