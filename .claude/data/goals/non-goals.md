# What This Product is NOT

## Explicit Exclusions

- **Practice Management Software**
  - *Reason: SyncoPaid is a time tracking app, not a client/matter management system. We import folder structures from the user's file system and use them as categories — we don't manage clients or matters.*
  - This means NO:
    - Creating, editing, or archiving clients/matters within the app
    - Contact information fields
    - Status management (Active, Closed, Archived)
    - Keywords or tags for auto-categorization
    - Parsing or interpreting folder/client/matter names
    - Moving matters between clients

- **Folder Name Parser**
  - *Reason: Lawyers have varying naming conventions for their folders. We don't try to extract or parse client names or matter names — we use folder names exactly as the user has them. This is unnecessary for our goal of categorizing time into categories that make sense to the user.*

- **Analytics & Reporting Dashboards**
  - *Reason: Analytics dashboards are what most app builders assume lawyers want, but sophisticated tables and reporting rarely provide valuable insights for time-tracking. The vision is to use AI to save lawyers time, not rebuild what already exists elsewhere.*

- **Standalone Screenshot Gallery/Viewer**
  - *Reason: Users can already open the screenshots folder via command. A dedicated browsing UI is unnecessary overhead.*
  - *Note: Could be reconsidered IF reframed as an AI-assisted clarification tool (e.g., when AI cannot categorize time, show screenshots to prompt user: "What file were you working on here?"). The gallery would serve AI workflows, not standalone browsing.*

- **Quick Actions Popup with Hotkeys**
  - *Reason: This app is meant to run in the background and be un-intrusive. Global hotkeys could interfere with the user's actual workflow tools.*

## Anti-Patterns to Avoid

- **Rebuilding Existing Tools**: Don't create features that lawyers already have elsewhere (reporting, visualization, complex analytics, practice management)
- **Replacing User Workflows**: Don't make users recreate their folder structure in the app — import what they already have
- **Over-Engineering Data Entry**: Don't add fields for data we don't need (contact info, matter status, etc.)
- **Intrusive UI Elements**: No popup overlays, global hotkeys, or interruptions during work
- **Feature Bloat Based on Assumptions**: Don't build what "most app builders assume lawyers want" — focus on actual user needs
- **Complex Configuration**: Avoid premature optimization settings that add complexity without clear value

## YAGNI Items

- **Screenshot Quality Optimization**
  - Configurable JPEG quality levels, WebP formats, resolution scaling, per-monitor settings
  - *Why: Unnecessary complexity before we know storage is actually a problem*

- **Quick Actions System**
  - Keyboard-activated popups for common tasks
  - *Why: Background apps should stay in the background*

## Philosophical Boundaries

**What This Product IS:**
- A **time tracking app** — nothing more
- An un-intrusive background time tracker
- An AI-powered billing assistant that saves lawyer time
- A tool that fits into the user's existing workflow
- Focused on capture and intelligent categorization

**What This Product is NOT:**
- Practice management software
- A client/matter management system
- A productivity analytics platform
- A screenshot management system
- An interactive overlay or hotkey-driven tool
- A replacement for existing legal practice management software

**Core Principle**: Use AI to eliminate manual work, not to add more features that require manual interaction. Stay invisible, capture accurately, categorize intelligently. Use what the user already has (their folder structure) rather than making them recreate it.

---
*Auto-generated from rejected story nodes in story-tree.db*
*Last updated: 2025-12-17 00:00 UTC*
