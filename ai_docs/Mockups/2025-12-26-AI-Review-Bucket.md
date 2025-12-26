# AI Review Timeline - Bucket Assignments

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](../Navigation/2025-12-25-Navigation-Index.md)

---

## Purpose

This view shows **AI-proposed bucket (matter) assignments** for captured activities. Users see what the AI suggests and its confidence level. Clicking an activity opens the full-context Review Interface for accept/reject decisions.

**Key principle:** This view shows AI proposals. Actual decisions happen in the [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) where full context (screenshots, reasoning) is visible.

---

## Menu Access

- **View → AI Review → By Matter** (Ctrl+3)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  File    Edit    View    Tools    Help                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  [▶ Tracking]   [Today ▼]   Filter: [All ▼] [Needs Review ▼]                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AI REVIEW - Matter Assignments                                             │
│  Click any activity to review with full context                             │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│  Smith v. Jones (3 activities)                                              │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  8:00 AM ─────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 8:02  ████████████████████████████████████████  Word - Contract.docx    │
│  │        │◄─────────────── 1h 23m ───────────────►│                        │
│  │        Confidence: ●●●●○ 85%                     [Review →]              │
│  │                                                                          │
│  ├─ 10:25 ████████████████████████████████████████████████████████████████  │
│  │        Chrome - CanLII - Smith v. Jones precedents                       │
│  │        │◄──────────────────── 2h 10m ─────────────────────►│             │
│  │        Confidence: ●●●●● 96%                     [Review →]              │
│  │                                                                          │
│  ═══════════════════════════════════════════════════════════════════════    │
│  Acme Corp / Contract Review (1 activity)                                   │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ├─ 1:15  ████████████████████████████  Word - Acme_NDA_final.docx          │
│  │        │◄────────── 1h 15m ──────────►│                                  │
│  │        Confidence: ●●●●○ 82%                     [Review →]              │
│  │                                                                          │
│  ═══════════════════════════════════════════════════════════════════════    │
│  ⚠ Needs Review (2 activities)                                              │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ├─ 9:40  ████████████████████████████  Outlook - RE: Settlement offer      │
│  │        │◄────────── 45m ──────────►│                                     │
│  │        Confidence: ●●○○○ 42% - Multiple matters mentioned                │
│  │        [Review →]                                                        │
│  │                                                                          │
│  ├─ 2:30  ████████████████████  Teams - Call with Sarah                     │
│  │        │◄────── 30m ──────►│                                             │
│  │        Confidence: ●○○○○ 23% - Cannot determine matter                   │
│  │        [Review →]                                                        │
│  │                                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tracking: Active │ Reviewed: 3/6 │ Needs Review: 2 │ High Confidence: 1    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Visual Organization

Activities are grouped by AI-suggested bucket, with a special section for items needing review.

| Section | Contents |
|---------|----------|
| **[Bucket Name]** | Activities AI assigned to this bucket |
| **⚠ Needs Review** | Low-confidence items requiring user input |

---

## Confidence Indicators

| Display | Level | Meaning |
|---------|-------|---------|
| ●●●●● 90-100% | Very High | AI very confident |
| ●●●●○ 70-89% | High | AI confident, may want to verify |
| ●●●○○ 50-69% | Medium | AI uncertain, review recommended |
| ●●○○○ 30-49% | Low | AI guessing, review needed |
| ●○○○○ <30% | Very Low | AI cannot determine |

---

## Filters

| Filter | Options |
|--------|---------|
| Matter | All, specific matter, or "Unassigned" |
| Status | All, Needs Review, Reviewed, High Confidence |

---

## Interactions

| Action | Result |
|--------|--------|
| Click activity or [Review →] | Opens Activity Review Interface with full context |
| Hover on confidence | Shows AI reasoning tooltip |
| Click bucket header | Collapse/expand that bucket's activities |

**What's NOT here:**
- No inline accept/reject buttons (decisions require full context)
- No editing (happens in Review Interface)
- No bulk selection checkboxes

---

## Activity Review Interface

When clicking [Review →], the Activity Review Interface opens showing:
- Full screenshots from the activity period
- AI's detailed reasoning for the suggestion
- Accept / Reject / Correct buttons
- Split activity option (with screenshot context)

See [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) for details.

---

## Status Bar

| Element | Description |
|---------|-------------|
| Tracking status | Active / Paused |
| Reviewed | Count of reviewed activities |
| Needs Review | Count requiring user input |
| High Confidence | Count AI is confident about |

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Move between activities |
| Enter | Open Review Interface for selected |
| Tab | Move between bucket sections |
| Ctrl+3 | Switch to this view |

---

## Related

- [Raw Timeline - Staircase](2025-12-26-Raw-Timeline-Staircase.md) - Raw captured data (no AI)
- [Raw Timeline - Table](2025-12-26-Raw-Timeline-Table.md) - Raw data in table format
- [AI Review - Narrative](2025-12-26-AI-Review-Narrative.md) - Review AI narrative suggestions
- [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) - Full-context review
