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

### Manual Activity Management
*Reason: Users should review AI suggestions, not manually organize activities. If users are doing the organizing, the AI isn't doing its job.*

This means NO:
- **Edit Narrative**: AI generates narratives; users accept or correct
- **Split Activity**: AI should detect activity boundaries
- **Merge Activities**: AI should recognize related work
- **Drag-and-drop reordering**: Activities are chronological facts
- **Manual bucket assignment as primary workflow**: Accept/reject AI suggestions instead

### List Management UI
*Reason: The Activities View redesign revealed that filter/sort/organize interfaces encourage manual management. The correct model is a review queue where AI presents suggestions.*

This means NO:
- Extensive sorting options (by app, duration, etc.)
- Complex multi-filter combinations
- Checkbox selection with bulk actions as primary interaction
- "Power user" table manipulation features

**Simple filters ARE okay**: By Bucket Group (Client), by Bucket (Matter), by date range. These help users focus on specific work. What's NOT okay is power-user table manipulation with complex filter chaining.

**Primary interaction**: Confidence-based filtering (show uncertain items), inline accept/reject.

### Folder Name Parser
*Reason: Lawyers have varying naming conventions for their folders. We don't try to extract or parse client names or matter names — we use folder names exactly as the user has them.*

### Analytics & Reporting Dashboards
*Reason: Analytics dashboards are what most app builders assume lawyers want, but sophisticated tables and reporting rarely provide valuable insights for time-tracking. The vision is to use AI to save lawyers time, not rebuild what already exists elsewhere.*

This means NO:
- Productivity analytics (hours per day charts, efficiency metrics)
- Complex pivot tables or data visualization
- Trend analysis or forecasting
- Customizable report builders

**Exception — Billing workflow reports ARE okay**: A simple "Billing Queue" showing which buckets have WIP that needs invoicing is aligned with the core workflow. This helps users identify what to bill, not analyze productivity. The distinction: analytics visualizes data for insight; billing queue drives action (send invoices).

### Standalone Screenshot Gallery/Viewer
*Reason: Screenshots serve AI clarification workflows, not standalone browsing.*

This means NO:
- Built-in screenshot browser or gallery
- Custom screenshot deletion UI
- Image viewer with zoom/pan controls

**The right approach**: Open the screenshots folder in Windows File Explorer. This provides:
- Real file deletion (users trust it actually deletes)
- Familiar Windows interface (no learning curve)
- Full control and transparency
- Less code to build and maintain

**In-app screenshot use**: When AI is uncertain, show relevant screenshots inline to prompt "What were you working on here?" Users don't browse screenshots; they answer specific questions.

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

### Dedicated Views for Actions
*Reason: Actions belong in menus, not as navigation destinations. Export is something you do, not somewhere you go.*

This means NO:
- Export View — use File → Export
- Analytics View — productivity dashboards are a non-goal
- Settings View — use File → Settings or Tools → Options
- Import View — use File → Import Folders

**Note**: A Billing Queue (showing WIP by bucket) is different from an "Analytics View" — it drives billing action, not data analysis. Whether it's a view or a menu action is a UI decision, not a philosophical one.

---

## Anti-Patterns to Avoid

### Management Over Review
- **Wrong**: Filter → Select → Assign to bucket → Save
- **Right**: AI suggests → User accepts or rejects

### Manual Effort as Features
- Don't add "Edit" buttons when AI should generate
- Don't add "Split/Merge" when AI should detect boundaries
- Don't add "Organize" when AI should categorize

### Terminology That Implies Management
See [CLAUDE.md Terminology](../../../CLAUDE.md#terminology) for approved terms. Avoid using "Matter", "Project", or "Case" in code/docs — these terms cause AI assistants to drift toward building management features.

### Rebuilding Existing Tools
Don't create features that lawyers already have elsewhere (reporting, visualization, complex analytics, practice management).

### Rebuilding Windows Functionality
Don't build custom viewers, file browsers, or deletion UIs when Windows already provides them. File Explorer is trusted, familiar, and actually deletes files. Standard Windows dialogs (file picker, date picker) are better than custom controls.

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

### Views for Everything
Don't create views for actions. Export, Settings, and Import are menu actions, not navigation destinations. Two views is enough: Timeline and Activities.

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
- An un-intrusive background time tracker
- An AI-powered billing assistant that saves lawyer time
- A tool that fits into the user's existing workflow
- A tool that leverages Windows (File Explorer, standard dialogs) rather than rebuilding
- Focused on capture, intelligent categorization, and billing workflow
- **Minimal views**: Timeline and Activities as core views; Billing Queue to drive invoicing action

**What This Product is NOT:**
- A **web/SaaS app** — no sidebars, tab bars, dashboards, or card layouts
- A **management workflow** — user organizes, filters, assigns
- Practice management software
- A client/matter management system
- A productivity analytics platform
- A custom screenshot browser (use File Explorer instead)
- An interactive overlay or hotkey-driven tool
- A power-user table manipulation tool
- A multi-view navigation app — actions belong in menus, not as views

---
*For terminology definitions, see [CLAUDE.md](../../../CLAUDE.md#terminology).*
*Last updated: 2025-12-26*
