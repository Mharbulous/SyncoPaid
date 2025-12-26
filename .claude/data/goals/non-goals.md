# What This Product is NOT

## Core Anti-Principle

> **If it requires manual effort, question whether the AI should handle it instead.**

The opposite of "The AI proposes, the user disposes" is "The user organizes, manages, and manually categorizes." We reject that model entirely.

---

## Explicit Exclusions

### Practice Management Software
*Reason: SyncoPaid is a time tracking app, not a client/matter management system. We import folder structures from the user's file system and use them as buckets — we don't manage clients or matters.*

This means NO:
- Creating, editing, or archiving buckets within the app
- Contact information fields
- Status management (Active, Closed, Archived)
- Keywords or tags for auto-categorization
- Parsing or interpreting folder/client/matter names
- Moving matters between clients

### Manual Activity Management as Primary Workflow
*Reason: Users should review AI suggestions, not manually organize activities. If users are doing the organizing, the AI isn't doing its job.*

**The key distinction:**
- **Primary workflow** (what we build for): AI proposes → user accepts/rejects
- **Exception handling** (what we allow): User corrects when AI is wrong

Corrections are valid. But if the UI makes corrections feel like the primary interaction, we've failed. The app should feel like reviewing a competent assistant's work, not doing the work yourself.

This means NO:
- **Manual bucket assignment as primary workflow**: Accept/reject AI suggestions instead
- **Drag-and-drop reordering**: Activities are chronological facts
- **Organizing/filtering as primary interaction**: Review queue, not list management

This means YES (as corrections):
- **Correct Bucket**: When AI assigned the wrong one
- **Adjust Boundaries**: When AI got start/end times wrong
- **Merge Activities**: When AI split something that should be one
- **Edit Narrative**: When AI-generated text needs adjustment

These are corrections to AI proposals, not primary workflows. They should feel like "fixing the exception" not "doing the work."

### List Management UI
*Reason: Filter/sort/organize interfaces encourage manual management. The Activities View exists for transparency — users verify their time is being captured accurately — not for list manipulation.*

**Activities View purpose:**
- Transparency: "Here's what the app captured"
- Verification: "Is this accurate?"
- Review: Accept/reject AI suggestions

**Not the purpose:**
- List management or "power user" table manipulation
- Extensive sorting/filtering as primary interaction
- Checkbox selection with bulk actions

This means NO:
- Extensive sorting options (by app, duration, etc.)
- Complex multi-filter combinations
- Checkbox selection with bulk actions as primary interaction
- "Power user" table manipulation features

Instead: Confidence-based filtering (show items needing review), inline accept/reject, chronological record for transparency.

### Folder Name Parser
*Reason: Lawyers have varying naming conventions for their folders. We don't try to extract or parse client names or matter names — we use folder names exactly as the user has them.*

### Analytics & Productivity Dashboards
*Reason: Analytics dashboards are what most app builders assume lawyers want, but sophisticated charts and productivity metrics rarely provide valuable insights for time-tracking.*

This means NO:
- Time-by-application charts
- Productivity trend graphs
- "Hours worked this week" summaries
- Comparative analytics (this week vs last week)
- Focus time / distraction metrics

**Important distinction**: This exclusion covers *analytics* (understanding patterns) — NOT *billing triage* (identifying what to bill). See [Billing Review in goals.md](goals.md#bill-get-paid) for the in-scope billing workflow.

| OUT OF SCOPE (Analytics) | IN SCOPE (Billing Triage) |
|--------------------------|---------------------------|
| "How productive was I?" | "What needs to be billed?" |
| Time-by-application charts | WIP accumulation by matter |
| Weekly productivity trends | Matters overdue for billing |
| Focus time analysis | Matters approaching budget |

### Standalone Screenshot Gallery/Viewer
*Reason: Screenshots serve AI clarification workflows, not standalone browsing.*

The only valid use: When AI is uncertain, show screenshots to prompt "What were you working on here?" Users don't browse screenshots; they answer specific questions.

### Quick Actions Popup with Hotkeys
*Reason: This app is meant to run in the background and be un-intrusive. Global hotkeys could interfere with the user's actual workflow tools.*

### Web/SaaS UI Patterns
*Reason: SyncoPaid is a Windows desktop app. Web patterns feel foreign and create cognitive friction.*

This means NO:
- Sidebars for navigation
- Tab bars or pill navigation
- Dashboard layouts with cards
- Floating action buttons
- Material Design or flat web aesthetics

### Views for Actions
*Reason: Actions belong in menus and open as dialogs, not as navigation destinations. Export is something you do, not somewhere you go.*

This means NO dedicated views for:
- Export — use File → Export... (dialog)
- Settings — use File → Settings or Tools → Options (dialog)
- Import — use File → Import Folders... (dialog)
- Billing Review — use File → Review Billing... (dialog)

**The distinction**:
- **View** = A navigation destination you switch to (like Timeline or Activities)
- **Dialog** = An action that opens a modal window, then closes when done

Two views is enough: Timeline and Activities. Everything else is a dialog.

---

## Anti-Patterns to Avoid

### Management Over Review
- **Wrong**: Filter → Select → Assign to bucket → Save
- **Right**: AI suggests → User accepts or rejects

### Primary Workflows That Should Be Corrections
- Don't make "Edit" the primary interaction — make it a correction to AI-generated content
- Don't make "Split/Merge" prominent — they're exceptions when AI missed boundaries
- Don't make "Assign Bucket" a dropdown selection — make it a correction to AI's suggestion
- The UI should make the happy path (accept AI) easier than the exception path (correct AI)

### Terminology That Implies Management
See [CLAUDE.md Terminology](../../../CLAUDE.md#terminology) for approved terms. Avoid using "Matter", "Project", or "Case" in code/docs — these terms cause AI assistants to drift toward building management features.

### Terminology That Implies User Must Act
Avoid terms that suggest the user is responsible for doing the work:
- **Wrong**: "Uncategorized" (implies user must categorize)
- **Right**: "Queued for AI" (implies AI will categorize)
- **Wrong**: "Unassigned" (implies user must assign)
- **Right**: "Pending AI" or "Awaiting AI" (implies AI will act)

Language should always point to AI as the actor, not the user.

### Rebuilding Existing Tools
Don't create features that lawyers already have elsewhere (productivity analytics, complex visualization, practice management).

### Replacing User Workflows
Don't make users recreate their folder structure in the app — import what they already have.

### Over-Engineering Data Entry
Don't add fields for data we don't need (contact info, matter status, etc.).

### Intrusive UI Elements
No popup overlays, global hotkeys, or interruptions during work.

### Feature Bloat Based on Assumptions
Don't build what "most app builders assume lawyers want" — focus on actual user needs.

### Complex Configuration
Avoid premature optimization settings that add complexity without clear value.

### Web UI Patterns in Desktop Apps
Don't use sidebars, tab bars, dashboards, or card layouts. SyncoPaid is a Windows desktop app — use menu bars, toolbars, and standard Windows controls.

### Analytics Disguised as Billing Tools
If a feature answers "how productive was I?" it's analytics (out of scope).
If a feature answers "what should I bill?" it's billing triage (in scope).

---

## YAGNI Items

### Screenshot Quality Optimization
Configurable JPEG quality levels, WebP formats, resolution scaling, per-monitor settings.
*Why: Unnecessary complexity before we know storage is actually a problem.*

### Quick Actions System
Keyboard-activated popups for common tasks.
*Why: Background apps should stay in the background.*

### Advanced Table Features
Column resizing, custom column ordering, saved views, export to CSV.
*Why: This is list management, not review workflow.*

---

## Philosophical Boundaries

**What This Product IS:**
- A **Windows desktop app** — menu bars, toolbars, standard Windows conventions
- A **review workflow** — AI proposes, user disposes
- A **billing assistant** — helps lawyers identify what to bill
- An un-intrusive background time tracker
- An AI-powered tool that saves lawyer time
- A tool that fits into the user's existing workflow
- Focused on capture, categorization, review, and billing
- **Two views only**: Timeline and Activities (everything else is a dialog)

**What This Product is NOT:**
- A **web/SaaS app** — no sidebars, tab bars, dashboards, or card layouts
- A **management workflow** — user organizes, filters, assigns
- A **productivity analytics platform** — no charts, trends, or metrics
- Practice management software
- A client/matter management system
- A screenshot browsing system
- An interactive overlay or hotkey-driven tool
- A power-user table manipulation tool
- A multi-view navigation app — actions open dialogs, not views

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
