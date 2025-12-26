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
- **Overdue Detection**: Identify matters that haven't been billed in a while
- **Budget Awareness**: Warn when matters approach budget limits (if budgets are set)
- **Export for Billing**: Export time entries in formats compatible with billing systems

*This is not analytics — it's actionable billing triage. The question isn't "how productive was I?" but "what should I bill?"*

### Setup (One-Time)
- **Import Folder Structure**: Import the user's existing folder structure from their file system. Folder names become buckets, used exactly as-is — no parsing or interpretation of naming conventions
- **Smart Prompting**: Non-intrusive AI that detects natural work transitions and prompts at appropriate moments

## Guiding Principles

1. **AI Proposes, User Disposes**: The AI does the work. Users confirm or correct. Every interaction should feel like reviewing, not doing.

2. **Transparency Builds Trust**: Users need to see that their time is being captured accurately. The UI should clearly show what the app is doing and what it has captured. This is especially important for first impressions — prospective users should immediately understand "this app works for me."

3. **Minimize Manual Effort**: Automate everything possible so lawyers can focus on legal work, not administrative tasks. If a feature requires manual effort, question whether the AI should handle it instead.

4. **Non-Intrusive Intelligence**: Run silently in the background. Prompt at natural breaks, never interrupt focused work.

5. **Use What Already Exists**: Import the user's existing folder structure rather than making them recreate it. Use their naming conventions as-is.

6. **Confidence-Based Attention**: Users shouldn't review everything equally. Surface what needs attention (uncertain items), let AI handle the rest.

7. **Context-Aware Categorization**: Capture rich contextual data (URLs, email subjects, folder paths) to enable accurate AI matching.

8. **Preserve All History**: Archive rather than delete — screenshots and activity data are valuable evidence, never throw them away.

9. **Lawyer-Specific Workflows**: Built for legal billing conventions (6-minute increments, matter/client structures, legal research sources like Westlaw/CanLII).

10. **Follow Platform Conventions**: Use standard Windows UI patterns. No sidebars, tab bars, or web/SaaS patterns in a desktop app.

11. **Self-Documenting Terminology**: Use terms that make clear who does the work. Prefer "Queued for AI" over "Uncategorized" — the former shows AI will act, the latter implies user must act. Language should reinforce the AI-driven philosophy throughout the UI.

12. **Focus on Getting Paid**: Features should help lawyers convert tracked time into billed time. If a feature doesn't support capture, categorization, review, or billing — question whether it belongs.

13. **Good Defaults Over Configuration**: The app should "just work" without requiring configuration. Every setting is a decision forced on the user. Prefer sensible defaults; only add settings when users genuinely need choice.

14. **Local-First AI**: Process data locally by default using local LLMs (Moondream). Cloud processing is opt-in with explicit consent. User data never leaves the machine unless the user explicitly chooses otherwise.

15. **Features Must Earn Inclusion**: Don't ask "Is this compatible with our goals?" — ask "Does this help achieve a goal?" If a feature doesn't actively advance capture, categorization, review, or billing, it doesn't belong. Being harmless isn't enough.

16. **Data Gathering Over Premature Optimization**: Don't build complex optimization features before knowing if they're needed. But DO include simple settings (quality, thresholds) that help gather data for future optimization decisions. The difference: premature optimization builds the solution; data gathering hooks help us discover what the solution should be.

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
