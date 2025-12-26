# Client Matters View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Client Matters View displays imported client/matter folders from the user's file system. These folder names serve as categories for time tracking - no parsing or interpretation of the names is performed.

---

## Menu Access

- **View → Client Matters** (F4)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Actions ─────────────────────────────────────────────────────────────┐  │
│  │ [📂 Import Folders]  [🔍 Search...]                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ FOLDER LIST ─────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Folder Name                                    Time Tracked          │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │  ▶ 2024-001 Acme Corp                              12.5 hrs           │  │
│  │    ├─ Contract Review                               8.2 hrs           │  │
│  │    └─ IP Licensing                                  4.3 hrs           │  │
│  │                                                                       │  │
│  │  ▶ 2024-002 Johnson                                67.8 hrs           │  │
│  │    ├─ Smith v Jones                                42.3 hrs           │  │
│  │    └─ Williams Estate                              25.5 hrs           │  │
│  │                                                                       │  │
│  │  ▶ Pro Bono                                         3.2 hrs           │  │
│  │    └─ Housing Clinic                                3.2 hrs           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Action Bar

| Button | Action |
|--------|--------|
| Import Folders | Browse to select client/matter folder structure |
| Search | Filter folder list by name |

---

## Folder List

Displays the imported folder hierarchy exactly as named by the user. Parent folders represent clients; subfolders represent matters.

### Columns

| Column | Description |
|--------|-------------|
| Folder Name | The folder name as it appears in the user's file system |
| Time Tracked | Total hours categorized to this folder |

### Interactions

| Action | Result |
|--------|--------|
| Click ▶ | Expand/collapse folder to show subfolders |
| Click folder | Select folder |
| Double-click folder | Navigate to Activities View filtered by this folder |

---

## Context Menu

Right-click on folder:

```
┌─────────────────────────┐
│  View Activities        │
│  View in Reports        │
│  ─────────────────────  │
│  Remove from List       │  ◄── Does not delete from file system
└─────────────────────────┘
```

---

## Import Folders Dialog

Opened via [Import Folders] button.

```
┌─────────────────────────────────────────┐
│  Import Client/Matter Folders     [✕]   │
├─────────────────────────────────────────┤
│                                         │
│  Select the root folder containing      │
│  your client/matter subfolders:         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ C:\Users\...\Clients            │[📁]│
│  └─────────────────────────────────┘    │
│                                         │
│  Preview:                               │
│  ┌─────────────────────────────────┐    │
│  │ ▶ 2024-001 Acme Corp            │    │
│  │   ├─ Contract Review            │    │
│  │   └─ IP Licensing               │    │
│  │ ▶ 2024-002 Johnson              │    │
│  └─────────────────────────────────┘    │
│                                         │
│                    [Cancel]  [Import]   │
└─────────────────────────────────────────┘
```

---

## Navigation Links

| From | To | Trigger |
|------|-----|---------|
| Folder | Activities View (filtered) | Double-click or context menu |
| Folder | Reports View (filtered) | Context menu → View in Reports |

---

## Related

- [Activities View](2025-12-25-Activities-View.md) - View activities by folder
- [Reports View](2025-12-25-Reports-View.md) - Time reports by folder
