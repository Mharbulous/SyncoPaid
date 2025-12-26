# Activities View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Activities View displays all tracked activities in a table/list format, enabling detailed filtering, sorting, and bulk operations.

---

## Menu Access

- **View → Activities** (F3)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Filters ─────────────────────────────────────────────────────────────┐  │
│  │ Status: [All ▼]  App: [All ▼]  Matter: [All ▼]  [🔍 Search...]       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Bulk Actions (when items selected) ──────────────────────────────────┐  │
│  │ ☑ 12 selected   [Assign Matter]  [🤖 Categorize]  [Delete]            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───┬──────────┬─────────────────────────────────┬──────────┬───────────┐  │
│  │ ☐ │ TIME     │ APPLICATION / TITLE             │ DURATION │ MATTER    │  │
│  ├───┼──────────┼─────────────────────────────────┼──────────┼───────────┤  │
│  │ ☐ │ 8:02 AM  │ 📝 Word - Contract_v3.docx      │ 1h 23m   │ Smith...  │  │
│  │ ☐ │ 9:25 AM  │ 💤 Idle                         │ 15m      │ —         │  │
│  │ ☐ │ 9:40 AM  │ 📧 Outlook - RE: Settlement     │ 45m      │ ⚠ None    │  │
│  │ ☐ │ 10:25 AM │ 🌐 Chrome - Legal Research      │ 2h 10m   │ Acme...   │  │
│  └───┴──────────┴─────────────────────────────────┴──────────┴───────────┘  │
│                                                                             │
│  Click row → Same ACTIVITY DETAIL panel as Timeline view                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Filter Bar

### Filter Dropdowns

| Filter | Options |
|--------|---------|
| Status | All, Categorized, Uncategorized, Idle |
| App | All, or specific applications |
| Matter | All, Unassigned, or specific matter |

### Search

- Searches across application name, window title, and narrative
- Real-time filtering as you type

### Menu Access

Filters can also be set via **View → Filter** submenu.

---

## Table Columns

| Column | Description | Sortable |
|--------|-------------|----------|
| ☐ | Selection checkbox | No |
| TIME | Start time of activity | Yes |
| APPLICATION / TITLE | App icon, name, and window title | Yes |
| DURATION | Length of activity | Yes |
| MATTER | Assigned matter or status | Yes |

### Column Sorting

- Click column header to sort ascending
- Click again to sort descending
- Click third time to remove sort

---

## Bulk Actions Bar

Appears when one or more activities are selected.

| Button | Action | Menu Equivalent |
|--------|--------|-----------------|
| Assign Matter | Opens Matter Picker for batch assign | Edit → Assign to Matter (Ctrl+M) |
| Categorize | Run AI on selected activities | Tools → Auto-Categorize (Ctrl+G) |
| Delete | Delete selected activities | Edit → Delete (Del) |

---

## Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| ⚠ None | Uncategorized activity (needs attention) |
| 💤 Idle | Idle period (no user activity) |
| — | Not applicable (e.g., idle periods) |
| ... | Text truncated (hover for full text) |

---

## Row Interactions

| Action | Result |
|--------|--------|
| Click row | Opens Activity Detail panel |
| Click checkbox | Toggles selection |
| Shift+Click | Select range |
| Ctrl+Click | Add to selection |
| Right-click | Context menu |
| Double-click | Opens Activity Detail in edit mode |

---

## Context Menu

Right-click on row(s):

```
┌─────────────────────────┐
│  Assign to Matter...    │  ◄── Ctrl+M
│  Edit Narrative...      │  ◄── Ctrl+E
│  ─────────────────────  │
│  Split Activity...      │
│  Merge Selected...      │
│  ─────────────────────  │
│  View Screenshots       │
│  ─────────────────────  │
│  Copy Details           │  ◄── Ctrl+C
│  ─────────────────────  │
│  Delete                 │  ◄── Del
└─────────────────────────┘
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Move row selection |
| Space | Toggle checkbox on selected row |
| Ctrl+A | Select all visible rows |
| Enter | Open Activity Detail for selected |
| Ctrl+M | Assign matter to selected |
| Del | Delete selected activities |
| Ctrl+F | Focus search field |

---

## Related

- [Timeline View](2025-12-25-Timeline-View.md) - Visual view of same data
- [Shared Components](2025-12-25-Shared-Components.md) - Matter Picker, Activity Detail
