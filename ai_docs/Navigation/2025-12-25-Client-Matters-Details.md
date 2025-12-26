# Client Matter Details

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Client Matter Details view shows information about a selected client or matter folder, including the folder path and time tracking summary.

---

## Menu Access

- Navigate from [Client Matters List](2025-12-25-Client-Matters-List.md) by clicking a row

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Actions ─────────────────────────────────────────────────────────────┐  │
│  │ [← Back to List]  [View Activities]  [View in Reports]                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ CLIENT MATTER DETAILS ───────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  2024-002 Johnson / Smith v Jones                                     │  │
│  │  ═══════════════════════════════════════════════════════════════════  │  │
│  │                                                                       │  │
│  │  Folder Path                                                          │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │  C:\Users\Brahm\Documents\Clients\2024-002 Johnson\Smith v Jones      │  │
│  │                                                                       │  │
│  │  Time Tracked                                                         │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │  Today:         1.5 hrs                                               │  │
│  │  This Week:     4.2 hrs                                               │  │
│  │  This Month:   18.5 hrs                                               │  │
│  │  Total:        42.3 hrs                                               │  │
│  │                                                                       │  │
│  │  Recent Activities                                                    │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │  Dec 25, 2025  10:30 AM    Word - Smith Motion.docx       0.5 hrs     │  │
│  │  Dec 25, 2025   9:15 AM    Outlook - RE: Smith case       0.3 hrs     │  │
│  │  Dec 24, 2025   3:45 PM    Word - Smith Motion.docx       1.2 hrs     │  │
│  │  Dec 24, 2025   1:00 PM    Chrome - Westlaw Research      2.1 hrs     │  │
│  │                                                                       │  │
│  │                                        [View All Activities →]        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Action Bar

| Button | Action |
|--------|--------|
| ← Back to List | Return to Client Matters List |
| View Activities | Navigate to Activities View filtered by this client/matter |
| View in Reports | Navigate to Reports View filtered by this client/matter |

---

## Details Panel

### Header

Displays the client/matter name as it appears in the folder structure.

### Folder Path

| Field | Description |
|-------|-------------|
| Folder Path | Full path to the folder on the user's file system |

### Time Tracked

| Metric | Description |
|--------|-------------|
| Today | Hours tracked today |
| This Week | Hours tracked this week |
| This Month | Hours tracked this month |
| Total | All-time hours for this client/matter |

### Recent Activities

Shows the most recent tracked activities categorized to this client/matter.

| Column | Description |
|--------|-------------|
| Date/Time | When the activity occurred |
| Application/Title | The tracked window title |
| Duration | Time spent on this activity |

---

## Navigation Links

| From | To | Trigger |
|------|-----|---------|
| ← Back to List | Client Matters List | Button click |
| View Activities | Activities View (filtered) | Button click |
| View in Reports | Reports View (filtered) | Button click |
| View All Activities → | Activities View (filtered) | Link click |

---

## Related

- [Client Matters List](2025-12-25-Client-Matters-List.md) - List of all client/matter folders
- [Activities View](2025-12-25-Activities-View.md) - View activities by client/matter
- [Reports View](2025-12-25-Reports-View.md) - Time reports by client/matter
