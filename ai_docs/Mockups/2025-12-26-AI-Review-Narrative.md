# AI Review Timeline - Narrative Descriptions

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](../Navigation/2025-12-25-Navigation-Index.md)

---

## Purpose

This view shows **AI-generated narrative descriptions** for captured activities. Users see billing-ready text that AI has drafted and its confidence level. Clicking an activity opens the full-context Review Interface for accept/edit decisions.

**Key principle:** This view shows AI-drafted narratives. Actual decisions happen in the [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) where full context (screenshots, reasoning) is visible.

---

## Menu Access

- **View → AI Review → By Narrative** (Ctrl+4)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  File    Edit    View    Tools    Help                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  [▶ Tracking]   [Today ▼]   Filter: [All ▼] [Needs Review ▼]                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AI REVIEW - Narrative Descriptions                                         │
│  Click any activity to review with full context                             │
│                                                                             │
│  8:00 AM ─────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 8:02  ████████████████████████████████████████  1h 23m                  │
│  │        Word - Contract_Draft_v3.docx                                     │
│  │        ┌─────────────────────────────────────────────────────────────┐   │
│  │        │ "Drafted and revised contract provisions regarding          │   │
│  │        │  indemnification clauses and liability limitations."        │   │
│  │        └─────────────────────────────────────────────────────────────┘   │
│  │        Narrative confidence: ●●●●○ 78%                   [Review →]      │
│  │                                                                          │
│  9:00 AM ─────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 9:40  ████████████████████████████  45m                                 │
│  │        Outlook - RE: Settlement offer                                    │
│  │        ┌─────────────────────────────────────────────────────────────┐   │
│  │        │ "Reviewed and responded to opposing counsel's settlement    │   │
│  │        │  proposal; analyzed terms and drafted counter-offer."       │   │
│  │        └─────────────────────────────────────────────────────────────┘   │
│  │        Narrative confidence: ●●●○○ 65%                   [Review →]      │
│  │                                                                          │
│  10:00 AM ────────────────────────────────────────────────────────────────  │
│  │                                                                          │
│  ├─ 10:25 ████████████████████████████████████████████████████████████████  │
│  │        Chrome - CanLII - Smith v. Jones precedents (2h 10m)              │
│  │        ┌─────────────────────────────────────────────────────────────┐   │
│  │        │ "Legal research on case precedents regarding contractual   │   │
│  │        │  obligations and breach remedies in similar matters."       │   │
│  │        └─────────────────────────────────────────────────────────────┘   │
│  │        Narrative confidence: ●●●●● 91%                   [Review →]      │
│  │                                                                          │
│  ═══════════════════════════════════════════════════════════════════════    │
│  ⚠ Needs Narrative Review                                                   │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ├─ 2:30  ████████████████████  30m                                         │
│  │        Teams - Call with Sarah                                           │
│  │        ┌─────────────────────────────────────────────────────────────┐   │
│  │        │ "Telephone conference regarding [unable to determine        │   │
│  │        │  subject matter from available context]."                   │   │
│  │        └─────────────────────────────────────────────────────────────┘   │
│  │        Narrative confidence: ●○○○○ 18% - Insufficient context            │
│  │        [Review →]                                                        │
│  │                                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tracking: Active │ Narratives: 4 │ Needs Review: 1 │ Ready to Export: 3    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Visual Elements

| Element | Description |
|---------|-------------|
| Time block | Visual duration indicator |
| Quoted box | AI-generated narrative text |
| Confidence dots | Narrative quality indicator |
| ⚠ Section | Items where AI couldn't generate good narrative |

---

## Confidence Indicators

| Display | Level | Meaning |
|---------|-------|---------|
| ●●●●● 90-100% | Very High | Narrative likely accurate and complete |
| ●●●●○ 70-89% | High | Narrative good, minor edits may help |
| ●●●○○ 50-69% | Medium | Narrative reasonable, review recommended |
| ●●○○○ 30-49% | Low | Narrative may be incomplete or vague |
| ●○○○○ <30% | Very Low | AI couldn't generate meaningful narrative |

---

## Filters

| Filter | Options |
|--------|---------|
| Confidence | All, High, Needs Review |
| Status | All, Pending, Reviewed, Exported |

---

## Interactions

| Action | Result |
|--------|--------|
| Click activity or [Review →] | Opens Activity Review Interface with full context |
| Hover on confidence | Shows AI reasoning for narrative choices |
| Hover on narrative | Shows full text if truncated |

**What's NOT here:**
- No inline text editing (editing requires screenshot context)
- No inline accept buttons (decisions require full context)
- No bulk approval checkboxes

---

## Activity Review Interface

When clicking [Review →], the Activity Review Interface opens showing:
- Screenshots from the activity period
- AI's reasoning for narrative word choices
- Accept / Edit / Regenerate buttons
- Full text editor for corrections

See [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) for details.

---

## Narrative Quality Factors

AI considers these when generating narratives:

| Factor | Impact on Confidence |
|--------|---------------------|
| Window title clarity | Higher if document names are descriptive |
| Application type | Higher for productivity apps (Word, Excel) |
| Screenshot content | Higher if text is readable |
| Activity duration | Higher for longer, focused activities |
| Context continuity | Higher if related to previous activities |

---

## Status Bar

| Element | Description |
|---------|-------------|
| Tracking status | Active / Paused |
| Narratives | Total activities with narratives |
| Needs Review | Count with low confidence |
| Ready to Export | Count approved for billing |

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑ ↓ | Move between activities |
| Enter | Open Review Interface for selected |
| Ctrl+4 | Switch to this view |

---

## Related

- [Raw Timeline - Staircase](2025-12-26-Raw-Timeline-Staircase.md) - Raw captured data (no AI)
- [Raw Timeline - Table](2025-12-26-Raw-Timeline-Table.md) - Raw data in table format
- [AI Review - Bucket](2025-12-26-AI-Review-Bucket.md) - Review AI bucket suggestions
- [Activity Review Interface](2025-12-26-Activity-Review-Interface.md) - Full-context review
