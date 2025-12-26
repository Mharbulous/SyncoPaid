# Timeline View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Timeline View is the default view when opening SyncoPaid. It displays activities as visual time blocks on a horizontal timeline, making it easy to see how time was spent throughout the day.

---

## Menu Access

- **View → Timeline** (F2)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Zoom ──────┐  ┌─ Filter ─────────────────┐  ┌─ Actions ──────────────┐  │
│  │ [−] Day [+] │  │ Apps: [All ▼] Matter: [▼]│  │ [🤖 Auto-Categorize]   │  │
│  └─────────────┘  └──────────────────────────┘  └────────────────────────┘  │
│                                                                             │
│  8am       9am       10am      11am      12pm      1pm       2pm           │
│  ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────    │
│  │         │         │         │         │         │         │             │
│  │ ████████████████  │ ████████████████████████████████████  │             │
│  │ Word - Contract   │ Outlook - Emails (Smith v. Jones)     │             │
│  │         │         │         │         │         │         │             │
│  │         │  ░░░░░░░░░░░░░░░░ │         │         │         │             │
│  │         │  Idle (15 min)    │         │         │         │             │
│  │         │         │         │         │         │         │             │
│  └─────────────────────────────────────────────────────────────────────────┘
│                                                                             │
│  Click block → Opens ACTIVITY DETAIL panel                                  │
│                                                                             │
│  ┌─ ACTIVITY DETAIL ───────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  Microsoft Word - Contract_Draft_v3.docx                            │    │
│  │  ─────────────────────────────────────────                          │    │
│  │  Duration: 1h 23m                                                   │    │
│  │  Time: 8:02 AM - 9:25 AM                                            │    │
│  │                                                                     │    │
│  │  Matter: [Smith v. Jones          ▼]  ◄── Inline assignment         │    │
│  │  Narrative: [Drafted contract provisions...]  ◄── Editable          │    │
│  │                                                                     │    │
│  │  [View Screenshots]  [Split Activity]  [Delete]                     │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Toolbar Components

### Zoom Controls

| Control | Action | Shortcut |
|---------|--------|----------|
| [−] | Zoom out (show more time) | Ctrl+- |
| Day | Reset to day view | Ctrl+0 |
| [+] | Zoom in (show less time) | Ctrl++ |

### Filter Dropdowns

| Filter | Options |
|--------|---------|
| Apps | All, or specific applications |
| Matter | All, Unassigned, or specific matter |

### Actions

| Button | Action | Menu Equivalent |
|--------|--------|-----------------|
| Auto-Categorize | Run AI categorization | Tools → Auto-Categorize (Ctrl+G) |

---

## Timeline Elements

### Activity Blocks

| Visual | Meaning |
|--------|---------|
| ████ Solid colored | Active work in an application |
| ░░░░ Hatched/faded | Idle time |
| ⚠ Warning indicator | Uncategorized activity |

### Block Interactions

| Action | Result |
|--------|--------|
| Hover | Shows tooltip with app, title, duration |
| Click | Opens Activity Detail panel |
| Right-click | Context menu (Assign, Split, Delete) |
| Drag edge | Adjust activity time boundaries |

---

## Activity Detail Panel

Opens when clicking an activity block.

### Fields

| Field | Description | Editable |
|-------|-------------|----------|
| Application | App name and window title | No |
| Duration | Time spent on activity | No |
| Time | Start and end time | No |
| Matter | Assigned legal matter | Yes (dropdown) |
| Narrative | Billing description | Yes (text field) |

### Actions

| Button | Action | Menu Equivalent |
|--------|--------|-----------------|
| View Screenshots | Opens screenshot gallery | Tools → View Screenshots |
| Split Activity | Opens split dialog | Edit → Split Activity |
| Delete | Removes activity | Edit → Delete (Del) |

---

## Context Menu

Right-click on activity block:

```
┌─────────────────────────┐
│  Assign to Matter...    │  ◄── Ctrl+M
│  Edit Narrative...      │  ◄── Ctrl+E
│  ─────────────────────  │
│  Split Activity...      │
│  Merge with Adjacent... │
│  ─────────────────────  │
│  View Screenshots       │
│  ─────────────────────  │
│  Delete                 │  ◄── Del
└─────────────────────────┘
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ← → | Move selection to adjacent activity |
| Enter | Open Activity Detail for selected |
| Ctrl+M | Assign matter to selected |
| Del | Delete selected activity |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |

---

## Related

- [Activities View](2025-12-25-Activities-View.md) - Table view of same data
- [Shared Components](2025-12-25-Shared-Components.md) - Matter Picker, Activity Detail
