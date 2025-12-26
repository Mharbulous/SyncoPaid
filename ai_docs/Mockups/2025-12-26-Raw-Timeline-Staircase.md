# Raw Data Timeline - Staircase View

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](../Navigation/2025-12-25-Navigation-Index.md)

---

## Purpose

This view provides **transparency** into what SyncoPaid captured. Users verify their time is being tracked accurately. This is a read-only display of raw captured data.

**This view does NOT:**
- Show AI interpretations (bucket assignments, narratives, confidence)
- Offer editing actions (those require context shown in Review views)
- Allow accept/reject decisions

---

## Menu Access

- **View → Raw Timeline → Staircase** (Ctrl+1)

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
│  8:00 AM ─────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 8:02  ██████████████████████████████████████████  Word - Contract.docx  │
│  │        │◄─────────────── 1h 23m ───────────────►│                        │
│  │                                                                          │
│  9:00 AM ─────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 9:25  ░░░░░░░░░░░░  Idle                                                │
│  │        │◄── 15m ──►│                                                     │
│  │                                                                          │
│  ├─ 9:40  ████████████████████████████  Outlook - RE: Settlement offer      │
│  │        │◄────────── 45m ──────────►│                                     │
│  │                                                                          │
│  10:00 AM ────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 10:25 ████████████████████████████████████████████████████████████████  │
│  │        Chrome - CanLII - Smith v. Jones precedents                       │
│  │        │◄──────────────────── 2h 10m ─────────────────────►│             │
│  │                                                                          │
│  ├─ 10:45 ⚡ Task switch detected                                           │
│  │                                                                          │
│  12:00 PM ────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tracking: Active │ Today: 4h 33m captured │ Queued for AI: 4 activities    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Visual Elements

| Element | Appearance | Meaning |
|---------|------------|---------|
| ████ Solid bar | Filled block | Active window time |
| ░░░░ Hatched bar | Gray hatched | Idle period |
| ⚡ Marker | Lightning icon | Task switch detected |
| Hour lines | Horizontal rule | Time reference |

---

## Data Shown (Raw Only)

| Data | Source | Example |
|------|--------|---------|
| Start time | Window tracker | 8:02 AM |
| Duration | Calculated | 1h 23m |
| Application | Window title | Word |
| Window title | Window title | Contract.docx |
| Idle periods | Idle detector | 15m idle |
| Task switches | Switch detector | ⚡ marker |

---

## Interactions

| Action | Result |
|--------|--------|
| Scroll | Navigate through timeline |
| Hover on bar | Tooltip shows full window title |
| Click hour marker | Jump to that time |

**What's NOT here:**
- No click-to-open detail panel (raw data is already visible)
- No right-click context menu (no actions available)
- No editing capabilities

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
| ↑ ↓ | Scroll timeline |
| Home | Jump to start of day |
| End | Jump to end of day |
| Ctrl+1 | Switch to this view |

---

## Related

- [Raw Timeline - Table](2025-12-26-Raw-Timeline-Table.md) - Same data in table format
- [AI Review - Bucket](2025-12-26-AI-Review-Bucket.md) - Review AI bucket suggestions
- [AI Review - Narrative](2025-12-26-AI-Review-Narrative.md) - Review AI narrative suggestions
