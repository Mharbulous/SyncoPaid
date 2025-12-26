# Billing Review Dialog

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Billing Review dialog helps lawyers identify matters that need billing attention. This is not an analytics dashboard — it's a focused tool for getting paid.

**Purpose:** Surface actionable billing items so lawyers can identify what to bill and when.

---

## Menu Access

- **File → Review Billing...** (Ctrl+B)

This is a **dialog** (action), not a view. It opens on top of the current view and closes when done.

---

## Layout

```
┌─ Review Billing ─────────────────────────────────────────────────── [X] ─┐
│                                                                          │
│  Matters needing attention:                                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  MATTER                    WIP         BUDGET      LAST BILLED    │  │
│  │  ══════════════════════════════════════════════════════════════    │  │
│  │  Smith v. Jones            $4,250      $5,000      45 days ago    │  │
│  │  Williams Estate           $2,800      $10,000     38 days ago    │  │
│  │  Acme Corp Merger          $1,950      $15,000     12 days ago    │  │
│  │  Henderson Contract        $8,200      $8,000      5 days ago     │  │
│  │  Davis Litigation          $650        —           3 days ago     │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Summary ──────────────────────────────────────────────────────────┐  │
│  │  Total unbilled WIP:            $17,850                            │  │
│  │  AI processing completed up to: 2025-12-24                         │  │
│  │  Matters overbudget:            1                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│                               [View Activities]  [Export for Billing]    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Columns

| Column | Description |
|--------|-------------|
| Matter | The matter name (from imported folder structure) |
| WIP | Unbilled work-in-progress dollar value |
| Budget | The matter's budget amount (— if no budget set) |
| Last Billed | Days since time was last marked as "Billed" |

---

## Sorting

Default sort: WIP amount descending (highest unbilled work first).

Users can click column headers to re-sort.

---

## Actions

| Button | Action |
|--------|--------|
| View Activities | Opens Activities view filtered to selected matter |
| Export for Billing | Exports selected matter's unbilled time for billing system import |

---

## Row Interaction

| Action | Result |
|--------|--------|
| Single-click | Selects the matter |
| Double-click | Opens Activities view filtered to that matter's WIP |

---

## Configuration

### Budget Tracking

Budgets are optional. If a matter has a budget set (via folder metadata or manual entry), the Budget column displays the amount. Matters without budgets show "—".

---

## What This Dialog is NOT

- **Not analytics**: No charts, graphs, or trend analysis
- **Not a view**: It's a dialog that opens and closes — doesn't replace Timeline or Activities
- **Not practice management**: We don't manage matters here — just surface billing needs

---

## Design Rationale

This dialog exists because **getting paid is a goal**. Lawyers need to know:

1. **What has accumulated WIP?** — Time tracked but not yet billed
2. **How current is AI processing?** — Date through which AI categorization is complete
3. **What's overbudget?** — Matters where WIP exceeds budget

This is not "analytics" — it's **actionable billing triage**.

---

## Related

- [Activities View](2025-12-25-Activities-View.md) - Review and export time entries
- [Export Dialog](2025-12-25-Export-View.md) - Export time for billing

---

## Terminology Note

This mockup uses "Matter" because it represents **user-facing UI**. In code and internal documentation, use "Bucket" per [CLAUDE.md terminology](../../../CLAUDE.md#terminology).
