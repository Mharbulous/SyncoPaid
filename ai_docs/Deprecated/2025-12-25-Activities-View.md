# Review Activities View

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Review Activities View is an **AI-first workflow** where users review and approve AI-proposed categorizations. The AI does the heavy lifting; users just confirm or correct.

**Philosophy**: Minimize manual effort. The AI proposes, the user disposes.

---

## Menu Access

- **View → Review Activities** (F3)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─ Review Queue ───────────────────────────────────────────────────────┐   │
│  │  🤖 AI has categorized 47 activities          [Review All]           │   │
│  │     23 high confidence  •  18 needs review  •  6 uncertain           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Filter ─────────────────────────────────────────────────────────────┐   │
│  │  Show: [Needs Review ▼]     Billing: [All ▼]                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────┬───────────────────────────────┬──────────┬────────────────┐   │
│  │ TIME     │ ACTIVITY                      │ DURATION │ AI SUGGESTION  │   │
│  ├──────────┼───────────────────────────────┼──────────┼────────────────┤   │
│  │ 8:02 AM  │ 📝 Word - Contract_v3.docx    │ 1h 23m   │ Smith/Estate   │   │
│  │          │                               │          │ ✓ Accept  ✗    │   │
│  ├──────────┼───────────────────────────────┼──────────┼────────────────┤   │
│  │ 9:40 AM  │ 📧 Outlook - RE: Settlement   │ 45m      │ ⚠ Uncertain    │   │
│  │          │                               │          │ [Assign...]    │   │
│  ├──────────┼───────────────────────────────┼──────────┼────────────────┤   │
│  │ 10:25 AM │ 🌐 Chrome - CanLII Research   │ 2h 10m   │ Acme/Litigation│   │
│  │          │                               │          │ ✓ Accept  ✗    │   │
│  └──────────┴───────────────────────────────┴──────────┴────────────────┘   │
│                                                                             │
│  ┌─ Batch Actions ──────────────────────────────────────────────────────┐   │
│  │  [✓ Accept All High Confidence]    [Mark as Non-Billable]            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Review Queue Summary

Shows AI categorization status at a glance:

| Badge | Meaning |
|-------|---------|
| **High confidence** | AI is confident; one-click accept |
| **Needs review** | AI has a suggestion but wants confirmation |
| **Uncertain** | AI needs user input (may show screenshots) |

**[Review All]** button starts guided review flow.

---

## Filter Options

| Filter | Options |
|--------|---------|
| Show | All, Needs Review, Uncertain Only, Accepted, Rejected |
| Billing | All, WIP, Billed, Non-Billable |

Filters help focus on what needs attention. Default: **Needs Review**.

---

## Table Columns

| Column | Description |
|--------|-------------|
| TIME | Start time of activity |
| ACTIVITY | App icon, name, and window title |
| DURATION | Length of activity |
| AI SUGGESTION | Proposed category + accept/reject actions |

---

## AI Suggestion Column

Each row shows the AI's proposed categorization with inline actions:

### High/Medium Confidence
```
┌────────────────┐
│ Smith/Estate   │  ◄── AI's suggested category (folder path)
│ ✓ Accept  ✗    │  ◄── One-click accept or reject
└────────────────┘
```

### Uncertain (needs user help)
```
┌────────────────┐
│ ⚠ Uncertain    │  ◄── AI couldn't determine
│ [Assign...]    │  ◄── Opens category picker
│ [📷 Context]   │  ◄── Show screenshots for clarification
└────────────────┘
```

---

## Billing Status

After accepting a categorization, user sets billing status:

| Status | Meaning |
|--------|---------|
| **WIP** | Work in progress (default for accepted items) |
| **Billed** | Already invoiced to client |
| **Non-Billable** | Not billable (admin, personal, etc.) |

Billing status can be set individually or in batch via **[Mark as Non-Billable]**.

---

## Batch Actions

| Button | Action |
|--------|--------|
| **Accept All High Confidence** | Approve all high-confidence suggestions at once |
| **Mark as Non-Billable** | Set selected activities as non-billable |

---

## Row Interactions

| Action | Result |
|--------|--------|
| **✓ Accept** | Approve AI suggestion, mark as WIP |
| **✗ Reject** | Dismiss suggestion, opens category picker |
| **[Assign...]** | Open category picker for uncertain items |
| **[📷 Context]** | Show screenshots to help identify the work |
| Click row | Expand to show activity details |

---

## Screenshot-Assisted Review

When AI is uncertain, clicking **[📷 Context]** shows relevant screenshots:

```
┌─────────────────────────────────────────────────────────────────┐
│  📷 What were you working on?                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ [9:40 AM]   │  │ [9:52 AM]   │  │ [10:15 AM]  │              │
│  │ screenshot  │  │ screenshot  │  │ screenshot  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                 │
│  Assign to: [Select category...  ▼]                             │
└─────────────────────────────────────────────────────────────────┘
```

This helps users identify ambiguous activities without leaving the review flow.

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Move between activities |
| Enter | Accept AI suggestion |
| Backspace | Reject suggestion |
| A | Accept all high confidence |
| N | Mark selected as non-billable |

---

## Idle Periods

Idle periods (💤) are shown but **not categorized by AI**. They appear grayed out with option to:
- Dismiss (ignore)
- Assign to a category (if the idle was actually thinking time)

---

## Related

- [Timeline View](2025-12-25-Timeline-View.md) - Visual chronological view
- [Shared Components](2025-12-25-Shared-Components.md) - Category Picker, Activity Detail
