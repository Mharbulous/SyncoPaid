# Shared Components

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

This document describes reusable UI components that appear across multiple views in SyncoPaid.

---

## Bucket Picker

Reusable component for assigning buckets (matters) to activities. Shows the user's imported folder structure exactly as-is.

*Note: Called "Bucket Picker" internally; displays as "Matter" in user-facing labels per [terminology guidelines](../../CLAUDE.md#terminology).*

### Appearance

```
┌───────────────────────────────────────┐
│  Assign to Matter                     │
│  ┌─────────────────────────────────┐  │
│  │ 🔍 Search matters...            │  │
│  └─────────────────────────────────┘  │
│                                       │
│  RECENT                               │
│  ├─ Smith v. Jones                    │
│  ├─ Acme Corp Merger                  │
│  └─ Williams Estate                   │
│                                       │
│  ALL FOLDERS                          │
│  ├─ ▶ ClientA (2)                     │
│  │   ├─ Smith v. Jones                │
│  │   └─ Williams Estate               │
│  ├─ ▶ ClientB (2)                     │
│  │   ├─ Acme Corp Merger              │
│  │   └─ Johnson Contract              │
│  └─ ▶ Pro Bono (1)                    │
│      └─ Legal Aid Clinic              │
│                                       │
└───────────────────────────────────────┘
```

### Key Characteristics

| Characteristic | Implementation |
|----------------|----------------|
| **Mirrors folder structure** | Shows imported folders exactly as user has them |
| **No create/edit** | Users cannot create folders here — that's done in their file system |
| **Collapsible tree** | Folder hierarchy is expandable/collapsible |
| **Search** | Filters across all folder names |
| **Recent** | Shows recently used folders for quick access |

### Used In

- [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) — Correction flow
- [Timeline View](2025-12-25-Timeline-View.md) — Activity detail panel

### Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Navigate list |
| → | Expand folder |
| ← | Collapse folder |
| Enter | Select highlighted item |
| Esc | Close picker |
| Type | Filter by search |

---

## Activity Detail Panel

Panel showing full details of a selected activity. Used for viewing activity information; major edits happen in the [Activity Review Interface](2025-12-26-Activity-Review-Interface.md).

### Appearance

```
┌─ ACTIVITY DETAIL ───────────────────────────────────────────────────┐
│                                                                     │
│  Microsoft Word - Contract_Draft_v3.docx                            │
│  ─────────────────────────────────────────                          │
│  Duration: 1h 23m                                                   │
│  Time: 8:02 AM - 9:25 AM                                            │
│                                                                     │
│  Matter: Smith v. Jones                                             │
│  Status: Queued for AI  |  Pending Review  |  Categorized           │
│                                                                     │
│  [View Screenshots]                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Fields

| Field | Type | Notes |
|-------|------|-------|
| Application / Title | Display | Window title captured by tracker |
| Duration | Display | Calculated from start/end time |
| Time | Display | Start and end timestamps |
| Matter | Display | Assigned bucket (if any) |
| Status | Display | Current state in workflow |

### Actions

| Button | Action | Notes |
|--------|--------|-------|
| View Screenshots | Opens screenshots in context | Leads to review interface if edits needed |

### What's NOT Here

- **Split Activity**: Only available in [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) where screenshots provide the context needed to choose a split point
- **Delete**: Destructive action moved to overflow menu (⋮) or context menu
- **Inline editing**: Major changes go through review interface with full context

---

## Date Picker

Used in toolbar for filtering by date.

### Appearance

```
┌─────────────────────────────────────┐
│  ◀  December 2025  ▶               │
├─────────────────────────────────────┤
│  Su  Mo  Tu  We  Th  Fr  Sa        │
│   1   2   3   4   5   6   7        │
│   8   9  10  11  12  13  14        │
│  15  16  17  18  19  20  21        │
│  22 [23] 24  25  26  27  28        │
│  29  30  31                        │
├─────────────────────────────────────┤
│  [Today]  [This Week]  [Clear]     │
└─────────────────────────────────────┘
```

### Presets

| Preset | Selection |
|--------|-----------|
| Today | Current day |
| This Week | Monday to Sunday |
| Clear | Remove date filter |

---

## Confirmation Dialog

Standard confirmation for destructive actions.

### Appearance

```
┌─────────────────────────────────────────┐
│  ⚠ Delete Activity?              [✕]   │
├─────────────────────────────────────────┤
│                                         │
│  Are you sure you want to delete this   │
│  activity? This action cannot be        │
│  undone.                                │
│                                         │
│  "Microsoft Word - Contract_v3.docx"    │
│  Duration: 1h 23m                       │
│                                         │
│            [Cancel]  [Delete]           │
└─────────────────────────────────────────┘
```

### Used For

- Deleting activities
- Clearing captured data
- Resetting settings to defaults

### NOT Used For

- Deleting/archiving clients or matters (we don't manage these — they're imported folders)

---

## Status Indicators

Visual indicators for activity workflow state.

### States

| State | Display | Meaning |
|-------|---------|---------|
| Queued for AI | `○ Queued` | Captured, awaiting AI categorization |
| Pending Review | `◐ Review` | AI uncertain, needs user input |
| Categorized | `● Done` | AI or user assigned bucket |

### Color Coding (Optional)

| State | Color | Rationale |
|-------|-------|-----------|
| Queued for AI | Gray | Inactive, waiting |
| Pending Review | Yellow/Amber | Needs attention |
| Categorized | Green | Complete |

---

## Related

- [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) — Full-context review with screenshots
- [AI Transparency Summary](2025-12-26-AI-Transparency-Summary.md) — Shows what AI did
- [Timeline View](2025-12-25-Timeline-View.md)
- [Menu Bar](2025-12-25-Menu-Bar.md)
