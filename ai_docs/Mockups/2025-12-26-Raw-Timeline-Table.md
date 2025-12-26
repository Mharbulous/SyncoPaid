# Raw Data Timeline - Table View

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](../Navigation/2025-12-25-Navigation-Index.md)

---

## Purpose

This view provides **transparency** into what SyncoPaid captured, displayed as a chronological table. Users verify their time is being tracked accurately. This is a read-only display of raw captured data.

**This view does NOT:**
- Show AI interpretations (bucket assignments, narratives, confidence)
- Offer editing actions (those require context shown in Review views)
- Allow accept/reject decisions

---

## Menu Access

- **View → Raw Timeline → Table** (Ctrl+2)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  File    Edit    View    Tools    Help                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  [▶ Tracking]   [Today ▼]                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW TIMELINE - What SyncoPaid Captured                                     │
│                                                                             │
│  ┌──────────┬──────────┬───────────────────────────────────────┬──────────┐ │
│  │ START    │ END      │ APPLICATION / WINDOW                  │ DURATION │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 8:02 AM  │ 9:25 AM  │ Word - Contract_Draft_v3.docx         │ 1h 23m   │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 9:25 AM  │ 9:40 AM  │ ░ Idle                                │ 15m      │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 9:40 AM  │ 10:25 AM │ Outlook - RE: Settlement offer        │ 45m      │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 10:25 AM │ 10:45 AM │ Chrome - CanLII - Smith v. Jones...   │ 20m      │ │
│  │          │          │ ⚡ Task switch detected                │          │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 10:45 AM │ 12:35 PM │ Chrome - Westlaw - Contract law...    │ 1h 50m   │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 12:35 PM │ 1:15 PM  │ ░ Idle                                │ 40m      │ │
│  ├──────────┼──────────┼───────────────────────────────────────┼──────────┤ │
│  │ 1:15 PM  │ 2:30 PM  │ Word - Contract_Draft_v3.docx         │ 1h 15m   │ │
│  └──────────┴──────────┴───────────────────────────────────────┴──────────┘ │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tracking: Active │ Today: 5h 48m captured │ Queued for AI: 6 activities    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Columns

| Column | Description |
|--------|-------------|
| START | Activity start time |
| END | Activity end time |
| APPLICATION / WINDOW | App name and window title |
| DURATION | Length of activity |

---

## Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| ░ prefix | Idle period |
| ⚡ marker | Task switch detected during activity |
| Ellipsis (...) | Window title truncated (hover for full) |

---

## Data Shown (Raw Only)

| Data | Source |
|------|--------|
| Start/end times | Window tracker |
| Application name | Window title parsing |
| Window title | Raw capture |
| Duration | Calculated |
| Idle periods | Idle detector |
| Task switches | Switch detector |

---

## Interactions

| Action | Result |
|--------|--------|
| Scroll | Navigate through records |
| Hover on row | Shows full window title if truncated |
| Click column header | Sort by that column |

**What's NOT here:**
- No click-to-open detail panel
- No right-click context menu
- No editing capabilities
- No selection checkboxes

---

## Sorting

| Column | Sort behavior |
|--------|---------------|
| START | Chronological (default: newest first) |
| END | By end time |
| DURATION | By length |

---

## Toolbar

| Control | Function |
|---------|----------|
| Tracking toggle | Start/pause tracking |
| Date picker | Select date to view |

---

## Status Bar

| Element | Description |
|---------|-------------|
| Tracking status | Active / Paused |
| Daily total | Total captured time today |
| Queued for AI | Activities awaiting AI processing |

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Move between rows |
| Home | Jump to first row |
| End | Jump to last row |
| Ctrl+2 | Switch to this view |

---

## When to Use This View vs Staircase

| Use Table When | Use Staircase When |
|----------------|-------------------|
| Checking specific times | Seeing time patterns |
| Verifying a particular activity was captured | Understanding day flow |
| Looking for gaps | Visualizing duration proportions |

---

## Related

- [Raw Timeline - Staircase](2025-12-26-Raw-Timeline-Staircase.md) - Same data as visual blocks
- [AI Review - Bucket](2025-12-26-AI-Review-Bucket.md) - Review AI bucket suggestions
- [AI Review - Narrative](2025-12-26-AI-Review-Narrative.md) - Review AI narrative suggestions
