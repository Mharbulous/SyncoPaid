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
│  │  MATTER                    WIP         LAST BILLED    STATUS       │  │
│  │  ══════════════════════════════════════════════════════════════    │  │
│  │  ⚠ Smith v. Jones          $4,250      45 days ago    Overdue      │  │
│  │  ⚠ Williams Estate         $2,800      38 days ago    Overdue      │  │
│  │  ● Acme Corp Merger        $1,950      12 days ago    On track     │  │
│  │  ▲ Henderson Contract      $8,200      5 days ago     Near budget  │  │
│  │  ● Davis Litigation        $650        3 days ago     On track     │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ Summary ──────────────────────────────────────────────────────────┐  │
│  │  Total unbilled WIP:  $17,850                                      │  │
│  │  Matters overdue:     2                                            │  │
│  │  Matters near budget: 1                                            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│                               [View Activities]  [Export for Billing]    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| ⚠ | Overdue | No billing in 30+ days with accumulated WIP |
| ▲ | Near budget | WIP approaching matter budget (if set) |
| ● | On track | Recently billed or low WIP accumulation |

---

## Columns

| Column | Description |
|--------|-------------|
| Matter | The matter name (from imported folder structure) |
| WIP | Unbilled work-in-progress dollar value |
| Last Billed | Days since time was last marked as "Billed" |
| Status | Billing urgency indicator |

---

## Sorting

Default sort: Most urgent first (Overdue → Near budget → On track), then by WIP amount descending.

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

### Overdue Threshold

Default: 30 days since last billed activity.

Configurable via **File → Settings → Billing → Overdue threshold**

### Budget Tracking

Budgets are optional. If a matter has a budget set (via folder metadata or manual entry), the "Near budget" warning appears at 80% utilization.

---

## What This Dialog is NOT

- **Not analytics**: No charts, graphs, or trend analysis
- **Not a view**: It's a dialog that opens and closes — doesn't replace Timeline or Activities
- **Not practice management**: We don't manage matters here — just surface billing needs

---

## Design Rationale

This dialog exists because **getting paid is a goal**. Lawyers need to know:

1. **What has accumulated WIP?** — Time tracked but not yet billed
2. **What's overdue?** — Matters that haven't been billed in a while
3. **What's near budget?** — Matters approaching limits

This is not "analytics" — it's **actionable billing triage**.

---

## Related

- [Activities View](2025-12-25-Activities-View.md) - Review and export time entries
- [Export Dialog](2025-12-25-Export-View.md) - Export time for billing

---

## Terminology Note

This mockup uses "Matter" because it represents **user-facing UI**. In code and internal documentation, use "Bucket" per [CLAUDE.md terminology](../../../CLAUDE.md#terminology).
