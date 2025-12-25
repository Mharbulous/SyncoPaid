# Matters View

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Matters View allows management of legal matters, their associated clients, keywords for auto-categorization, and time summaries.

---

## Menu Access

- **View → Matters** (F4)
- **File → New Matter** (Ctrl+N) - Opens new matter dialog

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Actions ─────────────────────────────────────────────────────────────┐  │
│  │ [+ New Matter]  [📥 Import CSV]  [🔍 Search...]                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ MATTERS LIST ──────────────────┐  ┌─ MATTER DETAIL ─────────────────┐   │
│  │                                 │  │                                 │   │
│  │  ▶ Acme Corp                    │  │  Smith v. Jones                 │   │
│  │    ├─ Merger Agreement          │  │  ═════════════════════════════  │   │
│  │    └─ IP Licensing              │  │                                 │   │
│  │                                 │  │  Client: Johnson & Associates   │   │
│  │  ▶ Johnson & Associates         │  │  Status: Active                 │   │
│  │    ├─ Smith v. Jones  ◄─────────┼──┤  Created: Jan 15, 2024          │   │
│  │    └─ Williams Estate           │  │                                 │   │
│  │                                 │  │  ┌─ Keywords ────────────────┐  │   │
│  │  ▶ Pro Bono                     │  │  │ smith, jones, contract,   │  │   │
│  │    └─ Housing Clinic            │  │  │ deposition, discovery     │  │   │
│  │                                 │  │  │ [+ Add]                   │  │   │
│  │                                 │  │  └───────────────────────────┘  │   │
│  │                                 │  │                                 │   │
│  │                                 │  │  ┌─ Time Summary ────────────┐  │   │
│  │                                 │  │  │ This Week:    4.2 hrs     │  │   │
│  │                                 │  │  │ This Month:  18.5 hrs     │  │   │
│  │                                 │  │  │ Total:       42.3 hrs     │  │   │
│  │                                 │  │  │                           │  │   │
│  │                                 │  │  │ [View Activities] ────────┼───┐  │
│  │                                 │  │  └───────────────────────────┘  │   │
│  │                                 │  │                                 │   │
│  │                                 │  │  [Edit Matter]  [Archive]       │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                          │
                  Navigates to Activities view filtered by matter ────────┘
```

---

## Action Bar

| Button | Action | Menu Equivalent |
|--------|--------|-----------------|
| + New Matter | Opens new matter dialog | File → New Matter (Ctrl+N) |
| Import CSV | Opens file picker for matter import | File → Import → Import Matters (CSV) |
| Search | Filter matters list | — |

---

## Matters List (Left Panel)

Hierarchical tree view organized by client.

### Tree Structure

```
▶ Client Name
  ├─ Matter 1 (status)
  ├─ Matter 2 (status)
  └─ Matter 3 (status)
```

### Interactions

| Action | Result |
|--------|--------|
| Click ▶ | Expand/collapse client group |
| Click matter | Show matter detail panel |
| Right-click matter | Context menu |
| Double-click matter | Open edit dialog |
| Drag matter | Move to different client |

---

## Matter Detail Panel (Right Panel)

### Information Fields

| Field | Description | Editable |
|-------|-------------|----------|
| Matter Name | Name/title of the matter | Via Edit |
| Client | Associated client | Via Edit |
| Status | Active, Closed, Archived | Via Edit |
| Created | Date matter was created | No |

### Keywords Section

Keywords used for auto-categorization.

| Action | Result |
|--------|--------|
| [+ Add] | Add new keyword |
| Click keyword | Remove keyword |
| Type in field | Add multiple keywords (comma-separated) |

### Time Summary

| Metric | Description |
|--------|-------------|
| This Week | Hours tracked this week |
| This Month | Hours tracked this month |
| Total | All-time hours for matter |

### Actions

| Button | Action | Notes |
|--------|--------|-------|
| View Activities | Navigate to Activities filtered by this matter | Cross-view navigation |
| Edit Matter | Opens edit dialog | — |
| Archive | Archives the matter | Removes from active list |

---

## Context Menu

Right-click on matter:

```
┌─────────────────────────┐
│  Edit Matter...         │
│  ─────────────────────  │
│  View Activities        │
│  View in Reports        │
│  ─────────────────────  │
│  Add Keywords...        │
│  ─────────────────────  │
│  Move to Client...      │
│  ─────────────────────  │
│  Archive                │
│  Delete                 │  ◄── Requires confirmation
└─────────────────────────┘
```

---

## New Matter Dialog

Opened via File → New Matter (Ctrl+N) or [+ New Matter] button.

```
┌─────────────────────────────────────────┐
│  New Matter                       [✕]   │
├─────────────────────────────────────────┤
│                                         │
│  Matter Name:                           │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Client:                                │
│  ┌─────────────────────────────────┐    │
│  │ [Select or Create Client ▼]    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Keywords (optional):                   │
│  ┌─────────────────────────────────┐    │
│  │ Enter keywords, comma-separated │    │
│  └─────────────────────────────────┘    │
│                                         │
│                    [Cancel]  [Create]   │
└─────────────────────────────────────────┘
```

---

## Navigation Links

| From | To | Trigger |
|------|-----|---------|
| Matter detail | Activities View (filtered) | [View Activities] button |
| Matter detail | Reports View (filtered) | Context menu → View in Reports |

---

## Related

- [Clients View](2025-12-25-Clients-View.md) - Manage clients
- [Activities View](2025-12-25-Activities-View.md) - View activities by matter
- [Reports View](2025-12-25-Reports-View.md) - Time reports by matter
