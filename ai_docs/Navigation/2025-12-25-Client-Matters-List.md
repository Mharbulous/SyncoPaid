# Client Matters List

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Client Matters List displays imported client/matter folders from the user's file system. These folder names serve as categories for time tracking - no parsing or interpretation of the names is performed.

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
│  ┌─ CLIENT MATTER LIST ──────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Name                                           Time Tracked          │  │
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
| Search | Filter list by name |

---

## Client Matter List

Displays the imported folder hierarchy exactly as named by the user. Parent folders represent clients; subfolders represent matters.

### Columns

| Column | Description |
|--------|-------------|
| Name | The folder name as it appears in the user's file system |
| Time Tracked | Total hours categorized to this client/matter |

### Interactions

| Action | Result |
|--------|--------|
| Click ▶ | Expand/collapse to show matters |
| Click row | Navigate to Client Matter Details view |
| Double-click row | Navigate to Activities View filtered by this client/matter |

---

## Context Menu

Right-click on row:

```
┌─────────────────────────┐
│  View Details           │
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
| Row | Client Matter Details | Click or context menu → View Details |
| Row | Activities View (filtered) | Double-click or context menu |
| Row | Reports View (filtered) | Context menu → View in Reports |

---

## Related

- [Client Matter Details](2025-12-25-Client-Matters-Details.md) - Details for a selected client/matter
- [Activities View](2025-12-25-Activities-View.md) - View activities by client/matter
- [Reports View](2025-12-25-Reports-View.md) - Time reports by client/matter
