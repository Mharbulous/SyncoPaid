# What This Product is NOT

## Core Anti-Principle

> **If it requires manual effort, question whether the AI should handle it instead.**

The opposite of "The AI proposes, the user disposes" is "The user organizes, manages, and manually categorizes." We reject that model entirely.

---

## Explicit Exclusions

### Practice Management Software
*Reason: SyncoPaid is a time tracking app, not a client/matter management system. We import folder structures from the user's file system and use them as categories — we don't manage clients or matters.*

This means NO:
- Creating, editing, or archiving clients/matters within the app
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
- **Manual category assignment as primary workflow**: Accept/reject AI suggestions instead

### List Management UI
*Reason: The Activities View redesign revealed that filter/sort/organize interfaces encourage manual management. The correct model is a review queue where AI presents suggestions.*

This means NO:
- Extensive sorting options (by app, duration, etc.)
- Complex multi-filter combinations
- Checkbox selection with bulk actions as primary interaction
- "Power user" table manipulation features

Instead: Confidence-based filtering (show uncertain items), inline accept/reject.

### Folder Name Parser
*Reason: Lawyers have varying naming conventions for their folders. We don't try to extract or parse client names or matter names — we use folder names exactly as the user has them.*

### Analytics & Reporting Dashboards
*Reason: Analytics dashboards are what most app builders assume lawyers want, but sophisticated tables and reporting rarely provide valuable insights for time-tracking. The vision is to use AI to save lawyers time, not rebuild what already exists elsewhere.*

### Standalone Screenshot Gallery/Viewer
*Reason: Screenshots serve AI clarification workflows, not standalone browsing.*

The only valid use: When AI is uncertain, show screenshots to prompt "What were you working on here?" Users don't browse screenshots; they answer specific questions.

### Quick Actions Popup with Hotkeys
*Reason: This app is meant to run in the background and be un-intrusive. Global hotkeys could interfere with the user's actual workflow tools.*

---

## Anti-Patterns to Avoid

### Management Over Review
- **Wrong**: Filter → Select → Assign to Matter → Save
- **Right**: AI suggests → User accepts or rejects

### Manual Effort as Features
- Don't add "Edit" buttons when AI should generate
- Don't add "Split/Merge" when AI should detect boundaries
- Don't add "Organize" when AI should categorize

### Terminology That Implies Management
- **Wrong**: "Matter" (implies practice management)
- **Right**: "Category" or folder path (imports what exists)

### Rebuilding Existing Tools
Don't create features that lawyers already have elsewhere (reporting, visualization, complex analytics, practice management).

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
- A **review workflow** — AI proposes, user disposes
- An un-intrusive background time tracker
- An AI-powered billing assistant that saves lawyer time
- A tool that fits into the user's existing workflow
- Focused on capture and intelligent categorization

**What This Product is NOT:**
- A **management workflow** — user organizes, filters, assigns
- Practice management software
- A client/matter management system
- A productivity analytics platform
- A screenshot browsing system
- An interactive overlay or hotkey-driven tool
- A power-user table manipulation tool

---
*Last updated: 2025-12-26*
