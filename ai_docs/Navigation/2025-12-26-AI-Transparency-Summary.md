# AI Transparency Summary

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Purpose

This component provides **transparency** into what AI has done — building user trust by showing AI activity without requiring immediate action.

This is **not** a review interface. Users observe what happened; they don't make decisions here.

---

## When It Appears

The AI Transparency Summary appears after AI categorization runs (manually triggered or automatic). It confirms that AI worked and provides a high-level summary.

---

## Appearance

### Status Bar Notification (Subtle)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Timeline ▼]  [Today ▼]                                    [● Tracking]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           (Main content area)                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ AI categorized 18 of 24 activities. 6 need your review.  [Review Now]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Summary Dialog (On Request)

Accessed via Help → AI Activity Log or clicking status bar notification.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI ACTIVITY LOG                                                     [✕]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TODAY (December 26, 2025)                                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  2:30 PM  Categorized 18 activities                                         │
│           • 12 high-confidence (auto-applied)                               │
│           • 6 need review                                                   │
│                                                                             │
│  9:15 AM  Categorized 8 activities                                          │
│           • 7 high-confidence (auto-applied)                                │
│           • 1 needs review                                                  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  YESTERDAY                                                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  5:45 PM  Categorized 31 activities                                         │
│           • 28 high-confidence (auto-applied)                               │
│           • 3 needed review (2 accepted, 1 corrected)                       │
│                                                                             │
│                                                          [Close]            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Characteristics

| Characteristic | Implementation |
|----------------|----------------|
| **No action buttons** | Users observe, don't decide |
| **Historical log** | Shows past AI activity, not just current |
| **Outcome tracking** | Shows what happened to items needing review |
| **Non-intrusive** | Status bar notification, not modal popup |

---

## What This Component Does NOT Do

- Does not show individual activity details
- Does not allow accept/reject decisions
- Does not show checkboxes or selection controls
- Does not require user action to dismiss (status bar persists until reviewed)

---

## Navigation

| From | Action | To |
|------|--------|-----|
| Status bar notification | Click "Review Now" | [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) |
| Help menu | "AI Activity Log" | Summary Dialog (this component) |

---

## Related

- [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) — Where users make review decisions with full context
- [Shared Components](2025-12-26-Shared-Components.md) — Other reusable UI components
