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

## UI Philosophy

SyncoPaid follows standard Windows desktop conventions:

- **Standard Windows desktop layout**: Menu bar → Toolbar → Content → Status bar
- **Menu bar for navigation**: Switch views via View menu, not sidebars or tabs
- **Minimal views**: Timeline and Activities only — two views is enough
- **Actions as dialogs**: Export, Import, Settings, Billing Review are actions (dialogs), not destinations (views)
- **Toolbar for frequent controls**: Tracking toggle, date picker

## Target User
Lawyers who need to track billable hours across multiple matters and clients, particularly those frustrated with manual time entry and seeking to reduce administrative overhead while maintaining accurate billing records.

## Core Capabilities

### Capture (Background)
- **Automatic Activity Capture**: Continuous tracking of window activities, browser URLs, email subjects, and folder paths to build a complete picture of work performed
- **Screenshot-Based History**: Automatic screenshot capture with intelligent deduplication and monthly archiving to preserve context while managing disk space

### Categorize (AI)
- **AI-Powered Categorization**: Intelligent activity classification that matches activities to the user's imported buckets
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

1. **Stricter Inclusion Filter**: When evaluating features, ask "Does this help achieve a goal?" — not "Is it compatible with goals?" The bar is active contribution, not mere compatibility. Features that don't actively support capture, categorization, review, or billing don't belong.

2. **Transparency Builds Trust**: Users need to see that their time is being captured accurately. The UI should clearly show what the app is doing and what it has captured. This is especially important for first impressions — prospective users should immediately understand "this app works for me."

3. **Transparency and Review Are Distinct**: Transparency shows what happened (no user action required). Review enables decisions (user action required). These serve different purposes and require different interfaces:
   - **Transparency interface**: "AI categorized 18 activities" — informational, no buttons
   - **Review interface**: Shows activity + screenshots + AI reasoning → then accept/reject buttons

   Never conflate these. A summary of what AI did is not a review interface — it's transparency. Review requires showing the full context of what's being reviewed.

4. **Minimize Manual Effort**: Automate everything possible so lawyers can focus on legal work, not administrative tasks. If a feature requires manual effort, question whether the AI should handle it instead.

5. **Non-Intrusive Intelligence**: Run silently in the background. Prompt at natural breaks, never interrupt focused work.

6. **Use What Already Exists**: Import the user's existing folder structure rather than making them recreate it. Use their naming conventions as-is.

7. **Confidence-Based Attention**: Users shouldn't review everything equally. Surface what needs attention (uncertain items), let AI handle the rest.

8. **Context-Aware Categorization**: Capture rich contextual data (URLs, email subjects, folder paths) to enable accurate AI matching.

9. **Preserve All History**: Archive rather than delete — screenshots and activity data are valuable evidence, never throw them away.

10. **Lawyer-Specific Workflows**: Built for legal billing conventions (6-minute increments, matter/client structures, legal research sources like Westlaw/CanLII).

11. **Follow Platform Conventions**: Use standard Windows UI patterns. No sidebars, tab bars, or web/SaaS patterns in a desktop app.

12. **Self-Documenting Terminology**: Use terms that make clear who does the work. Prefer "Queued for AI" over "Uncategorized" — the former shows AI will act, the latter implies user must act. Language should reinforce the AI-driven philosophy throughout the UI.

13. **Focus on Getting Paid**: Features should help lawyers convert tracked time into billed time. If a feature doesn't support capture, categorization, review, or billing — question whether it belongs.

14. **Show Data, Not Computed Status**: Present facts (WIP amounts, budgets, dates) rather than derived interpretations (Overdue, On Track, Near Budget). Status calculations require complex logic, subjective thresholds, and edge case handling. Simple data lets users draw their own conclusions and avoids the app making judgment calls that may not match user expectations.

15. **Good Defaults Over Configuration**: Every setting is a decision forced on the user. If a sensible default exists, don't add the setting. Use system settings for theme, language, and date format. Avoid customization for the sake of customization.

16. **Local-First AI**: Default to local AI processing (Moondream). Cloud options are opt-in and require explicit user consent with clear warnings about data transmission.

17. **Data Gathering Over Premature Optimization**: Simple settings that enable future optimization decisions (quality %, thresholds) are acceptable. Complex optimization features that try to solve problems we haven't validated yet are not. Gather data first, optimize later.

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
