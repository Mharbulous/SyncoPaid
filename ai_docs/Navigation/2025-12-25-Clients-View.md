# Clients View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Clients View allows management of clients and their associated matters, with time summaries across all client work.

---

## Menu Access

- **View → Clients** (F5)
- **File → New Client** (Ctrl+Shift+N) - Opens new client dialog

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Actions ─────────────────────────────────────────────────────────────┐  │
│  │ [+ New Client]  [📥 Import CSV]  [🔍 Search...]                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ CLIENTS LIST ──────────────────┐  ┌─ CLIENT DETAIL ─────────────────┐   │
│  │                                 │  │                                 │   │
│  │  Acme Corp                      │  │  Johnson & Associates           │   │
│  │  Johnson & Associates  ◄────────┼──┤  ═════════════════════════════  │   │
│  │  Pro Bono                       │  │                                 │   │
│  │  Williams Family Trust          │  │  Contact: Robert Johnson        │   │
│  │                                 │  │  Added: Dec 10, 2023            │   │
│  │                                 │  │                                 │   │
│  │                                 │  │  ┌─ Matters ─────────────────┐  │   │
│  │                                 │  │  │ • Smith v. Jones (Active) │──┼───┐
│  │                                 │  │  │ • Williams Estate (Active)│  │   │
│  │                                 │  │  │                           │  │   │
│  │                                 │  │  │ [+ New Matter]            │  │   │
│  │                                 │  │  └───────────────────────────┘  │   │
│  │                                 │  │                                 │   │
│  │                                 │  │  ┌─ Time Summary ────────────┐  │   │
│  │                                 │  │  │ All Matters: 67.8 hrs     │  │   │
│  │                                 │  │  └───────────────────────────┘  │   │
│  │                                 │  │                                 │   │
│  │                                 │  │  [Edit Client]  [Archive]       │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                          │
                         Navigates to Matter detail view ─────────────────┘
```

---

## Action Bar

| Button | Action | Menu Equivalent |
|--------|--------|-----------------|
| + New Client | Opens new client dialog | File → New Client (Ctrl+Shift+N) |
| Import CSV | Opens file picker for client import | File → Import → Import Clients (CSV) |
| Search | Filter clients list | — |

---

## Clients List (Left Panel)

Simple alphabetical list of all clients.

### Interactions

| Action | Result |
|--------|--------|
| Click client | Show client detail panel |
| Right-click client | Context menu |
| Double-click client | Open edit dialog |

---

## Client Detail Panel (Right Panel)

### Information Fields

| Field | Description | Editable |
|-------|-------------|----------|
| Client Name | Name of the client | Via Edit |
| Contact | Primary contact person | Via Edit |
| Added | Date client was added | No |

### Matters Section

List of matters associated with this client.

| Element | Action |
|---------|--------|
| Matter name | Click to navigate to Matters View with that matter selected |
| (status) | Shows Active, Closed, or Archived |
| [+ New Matter] | Opens new matter dialog pre-filled with this client |

### Time Summary

| Metric | Description |
|--------|-------------|
| All Matters | Combined hours across all client matters |

### Actions

| Button | Action | Notes |
|--------|--------|-------|
| Edit Client | Opens edit dialog | — |
| Archive | Archives the client | Removes from active list |

---

## Context Menu

Right-click on client:

```
┌─────────────────────────┐
│  Edit Client...         │
│  ─────────────────────  │
│  Add New Matter...      │
│  ─────────────────────  │
│  View All Activities    │
│  View in Reports        │
│  ─────────────────────  │
│  Archive                │
│  Delete                 │  ◄── Requires confirmation
└─────────────────────────┘
```

---

## New Client Dialog

Opened via File → New Client (Ctrl+Shift+N) or [+ New Client] button.

```
┌─────────────────────────────────────────┐
│  New Client                       [✕]   │
├─────────────────────────────────────────┤
│                                         │
│  Client Name:                           │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Contact Name (optional):               │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Notes (optional):                      │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│                    [Cancel]  [Create]   │
└─────────────────────────────────────────┘
```

---

## Navigation Links

| From | To | Trigger |
|------|-----|---------|
| Client detail → Matter name | Matters View (with matter selected) | Click matter name |
| Client detail | New Matter dialog | [+ New Matter] button |
| Client context menu | Activities View (filtered) | View All Activities |
| Client context menu | Reports View (filtered) | View in Reports |

---

## Related

- [Matters View](2025-12-25-Matters-View.md) - Manage matters
- [Reports View](2025-12-25-Reports-View.md) - Time reports by client
