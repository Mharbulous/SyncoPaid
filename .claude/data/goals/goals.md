# Product Vision

## What We're Building
SyncoPaid is a time-tracking application for lawyers that automatically captures work activities and uses AI to categorize time into billing buckets with minimal manual effort.

## Core Philosophy

> **"The AI proposes, the user disposes."**

The AI does the heavy lifting. Users review and confirm — they don't organize, manage, or manually categorize. Every UI interaction should feel like approving a suggestion, not performing a task.

## What This App Is
- A **time tracking app** — not practice management software
- A **Windows desktop app** — following standard Windows conventions, not web/SaaS patterns
- A tool that **fits into the user's existing workflow** — not one that replaces it
- An app that uses the **user's own folder structure** as buckets (see [Terminology](../../../CLAUDE.md#terminology))
- A **review workflow** — not a management workflow

## UI Philosophy

SyncoPaid follows standard Windows desktop conventions:

- **Standard Windows desktop layout**: Menu bar → Toolbar → Content → Status bar
- **Menu bar for navigation**: Switch views via View menu, not sidebars or tabs
- **Minimal views**: Timeline and Activities only — two views is enough
- **Actions in menus**: Export, Import, Settings are actions, not destinations
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

### Setup (One-Time)
- **Import Folder Structure**: Import the user's existing folder structure from their file system. Folder names become buckets, used exactly as-is — no parsing or interpretation of naming conventions
- **Smart Prompting**: Non-intrusive AI that detects natural work transitions and prompts at appropriate moments

## Guiding Principles

1. **AI Proposes, User Disposes**: The AI does the work. Users confirm or correct. Every interaction should feel like reviewing, not doing.

2. **Minimize Manual Effort**: Automate everything possible so lawyers can focus on legal work, not administrative tasks. If a feature requires manual effort, question whether the AI should handle it instead.

3. **Non-Intrusive Intelligence**: Run silently in the background. Prompt at natural breaks, never interrupt focused work.

4. **Use What Already Exists**: Import the user's existing folder structure rather than making them recreate it. Use their naming conventions as-is.

5. **Confidence-Based Attention**: Users shouldn't review everything equally. Surface what needs attention (uncertain items), let AI handle the rest.

6. **Context-Aware Categorization**: Capture rich contextual data (URLs, email subjects, folder paths) to enable accurate AI matching.

7. **Preserve All History**: Archive rather than delete — screenshots and activity data are valuable evidence, never throw them away.

8. **Lawyer-Specific Workflows**: Built for legal billing conventions (6-minute increments, matter/client structures, legal research sources like Westlaw/CanLII).

9. **Follow Platform Conventions**: Use standard Windows UI patterns. No sidebars, tab bars, or web/SaaS patterns in a desktop app.

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
