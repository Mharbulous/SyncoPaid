# Product Vision

## What We're Building
SyncoPaid is a time-tracking application for lawyers that automatically captures work activities, uses AI to categorize time into billing buckets, and helps lawyers get paid by surfacing what needs to be billed.

## Core Philosophy

> **"The AI proposes, the user disposes."**

The AI does the heavy lifting. Users review and confirm — they don't organize, manage, or manually categorize. Every UI interaction should feel like approving a suggestion, not performing a task.

**"Disposes" means:**
- **Accept** what AI got right (the common case)
- **Reject** what doesn't belong
- **Correct** what AI got wrong (the exception, not the rule)

Corrections are valid user actions — but they're exception handling, not the primary workflow. If users are constantly correcting, the AI isn't doing its job.

> **"Context before action."**

Users cannot "dispose" of something they haven't seen. Every accept/reject/correct interface must first show users the information they need to make that decision: the activity details, screenshots, AI reasoning. Never offer action buttons without the context those actions depend on.

> **"Track time. Get paid."**

The app doesn't just track time — it helps lawyers turn tracked time into billed time. The "Paid" in SyncoPaid is intentional: the goal is revenue, not just records.

## What This App Is
- A **time tracking app** — not practice management software
- A **billing assistant** — helps lawyers identify what needs to be billed
- A **Windows desktop app** — following standard Windows conventions, not web/SaaS patterns
- A tool that **fits into the user's existing workflow** — not one that replaces it
- An app that uses the **user's own folder structure** as buckets (see [Terminology](../../../CLAUDE.md#terminology))
- A **review workflow** — not a management workflow

## Two Types of Data

The app handles two fundamentally different types of information:

### Raw Captured Data (What Happened)
- Window titles and application names
- Timestamps (start/end times)
- Duration
- Idle periods
- Task-switch markers
- Screenshots

This is **objective fact** — what SyncoPaid observed. It has no confidence level because it's not a prediction; it's a record.

### AI Interpretations (What AI Proposes)
- **Bucket assignment**: Which matter/folder does this activity belong to?
- **Narrative description**: What billing text describes this work?
- **Confidence levels**: How certain is AI about each proposal?

This is **AI proposal** — what the AI thinks the raw data means. Each interpretation has a confidence level because it's a prediction that could be wrong.

**Why this distinction matters:**
- Raw data views are for **transparency** (read-only, no editing)
- AI interpretation views are for **review** (lead to accept/reject decisions)
- Confidence applies only to AI interpretations, never to raw data
- Users can verify raw data is accurate (transparency) without making decisions
- Users make decisions only when reviewing AI proposals (with full context)

## UI Philosophy

SyncoPaid follows standard Windows desktop conventions:

- **Standard Windows desktop layout**: Menu bar → Toolbar → Content → Status bar
- **Menu bar for navigation**: Switch views via View menu, not sidebars or tabs
- **Four views organized by data type**:
  - **Raw Data Views** (transparency, read-only):
    - *Staircase*: Visual time blocks showing when activities happened
    - *Table*: Chronological list for verifying what was captured
  - **AI Review Views** (decisions, lead to full-context review):
    - *By Bucket*: AI-proposed matter assignments with confidence
    - *By Narrative*: AI-generated billing text with confidence
- **Actions as dialogs**: Export, Import, Settings, Billing Review are actions (dialogs), not destinations (views)
- **Toolbar for frequent controls**: Tracking toggle, date picker
- **Raw data views are read-only**: No editing actions — transparency means showing what happened, not changing it
- **AI review views lead to decisions**: Clicking an item opens the full-context Review Interface where accept/reject/correct happens

## Target User
Lawyers who need to track billable hours across multiple matters and clients, particularly those frustrated with manual time entry and seeking to reduce administrative overhead while maintaining accurate billing records.

## Core Capabilities

### Capture (Background)
- **Automatic Activity Capture**: Continuous tracking of window activities, browser URLs, email subjects, and folder paths to build a complete picture of work performed
- **Screenshot-Based History**: Automatic screenshot capture with intelligent deduplication and monthly archiving to preserve context while managing disk space
- **User-Initiated Markers**: One-click "stopwatch reset" via system tray left-click lets users mark task transitions or interruptions — AI uses these markers alongside automatic detection to improve categorization accuracy

### Categorize (AI)
- **AI-Powered Categorization**: Intelligent activity classification that matches activities to the user's imported buckets
- **AI-Generated Narratives**: Billing-ready text descriptions of what work was performed, derived from window titles, screenshots, and context
- **Dual Confidence Levels**: AI reports separate confidence for bucket assignment and narrative quality — an activity might have high bucket confidence but low narrative confidence (or vice versa)
- **Confidence-Based Triage**: AI communicates its confidence level (high confidence, needs review, uncertain) so users focus attention where it's needed
- **Continuous Learning**: AI improves accuracy by learning from user corrections and building bucket-specific patterns

### Review (User)
- **Accept/Reject Workflow**: Users approve or reject AI suggestions with one click — not manually assign buckets
- **Screenshot-Assisted Clarification**: When AI is uncertain, show relevant screenshots to help users identify the work: "What were you working on here?"
- **Batch Approval**: Accept all high-confidence suggestions at once to minimize clicks
- **Billing Status Tracking**: Mark time as WIP, Billed, or Non-Billable

### Bill (Get Paid)
- **Billing Review**: Surface matters with accumulated WIP that need to be billed
- **Budget Visibility**: Show matter budgets alongside WIP so users can see what's overbudget
- **AI Processing Status**: Show the date through which AI categorization is complete
- **Export for Billing**: Export time entries in formats compatible with billing systems

*This is not analytics — it's actionable billing triage. Present facts (WIP, Budget, Last Billed), not computed interpretations (Overdue, On Track). Let users draw conclusions from the data.*

### Setup (One-Time)
- **Import Folder Structure**: Import the user's existing folder structure from their file system. Folder names become buckets, used exactly as-is — no parsing or interpretation of naming conventions
- **Smart Prompting**: Non-intrusive AI that detects natural work transitions and prompts at appropriate moments

## Guiding Principles

1. **AI Proposes, User Disposes**: The AI does the work. Users confirm or correct. Every interaction should feel like reviewing, not doing.

2. **Stricter Inclusion Filter**: When evaluating features, ask "Does this help achieve a goal?" — not "Is it compatible with goals?" The bar is active contribution, not mere compatibility. Features that don't actively support capture, categorization, review, or billing don't belong.

3. **Transparency Builds Trust**: Users need to see that their time is being captured accurately. The UI should clearly show what the app is doing and what it has captured. This is especially important for first impressions — prospective users should immediately understand "this app works for me."

4. **Transparency and Review Are Distinct**: Transparency shows what happened (no user action required). Review enables decisions (user action required). These serve different purposes and require different interfaces:
   - **Transparency interface**: "AI categorized 18 activities" — informational, no buttons
   - **Review interface**: Shows activity + screenshots + AI reasoning → then accept/reject buttons

   Never conflate these. A summary of what AI did is not a review interface — it's transparency. Review requires showing the full context of what's being reviewed.

5. **Raw Data Views Are Read-Only**: Views that display raw captured data exist for transparency — users verify their time is being captured accurately. These views have no editing actions because:
   - Transparency means showing what happened, not changing it
   - Any editing action (split, delete, assign) requires context not present in raw data views
   - Decisions belong in the Review Interface where full context (screenshots, AI reasoning) is visible

   If a view shows raw data, it should have no action buttons. If a view needs action buttons, it should show AI proposals with full context.

6. **Minimize Manual Effort**: Automate everything possible so lawyers can focus on legal work, not administrative tasks. If a feature requires manual effort, question whether the AI should handle it instead.

7. **Non-Intrusive Intelligence**: Run silently in the background. Prompt at natural breaks, never interrupt focused work.

8. **Use What Already Exists**: Import the user's existing folder structure rather than making them recreate it. Use their naming conventions as-is. When implementing features, prefer modifying existing code over adding new infrastructure.

9. **Minimal Friction for Frequent Actions**: The most common user actions should require the fewest clicks. System tray left-click is reserved for the single most important quick action (marking task transitions). No dialogs, no confirmations — just instant effect.

10. **Confidence-Based Attention**: Users shouldn't review everything equally. Surface what needs attention (uncertain items), let AI handle the rest.

11. **Context-Aware Categorization**: Capture rich contextual data (URLs, email subjects, folder paths) to enable accurate AI matching.

12. **Preserve All History**: Archive rather than delete — screenshots and activity data are valuable evidence, never throw them away.

13. **Lawyer-Specific Workflows**: Built for legal billing conventions (6-minute increments, matter/client structures, legal research sources like Westlaw/CanLII).

14. **Follow Platform Conventions**: Use standard Windows UI patterns. No sidebars, tab bars, or web/SaaS patterns in a desktop app.

15. **Self-Documenting Terminology**: Use terms that make clear who does the work. Prefer "Queued for AI" over "Uncategorized" — the former shows AI will act, the latter implies user must act. Language should reinforce the AI-driven philosophy throughout the UI.

16. **Focus on Getting Paid**: Features should help lawyers convert tracked time into billed time. If a feature doesn't support capture, categorization, review, or billing — question whether it belongs.

17. **Show Data, Not Computed Status**: Present facts (WIP amounts, budgets, dates) rather than derived interpretations (Overdue, On Track, Near Budget). Status calculations require complex logic, subjective thresholds, and edge case handling. Simple data lets users draw their own conclusions and avoids the app making judgment calls that may not match user expectations.

18. **Good Defaults Over Configuration**: Every setting is a decision forced on the user. If a sensible default exists, don't add the setting. Use system settings for theme, language, and date format. Avoid customization for the sake of customization.

19. **Local-First AI**: Default to local AI processing (Moondream). Cloud options are opt-in and require explicit user consent with clear warnings about data transmission.

20. **Data Gathering Over Premature Optimization**: Simple settings that enable future optimization decisions (quality %, thresholds) are acceptable. Complex optimization features that try to solve problems we haven't validated yet are not. Gather data first, optimize later.

21. **Simplicity Over Cleverness (KISS)**: Prefer simple solutions that modify existing code over creating new infrastructure. Every new module, class, or abstraction must justify its existence. If a feature can be implemented by changing 10 lines in an existing file, don't create a new 100-line module.

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
