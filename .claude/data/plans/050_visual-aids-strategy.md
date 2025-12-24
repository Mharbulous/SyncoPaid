# Create Visual Aids Strategy - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.6 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a visual aids strategy document that enables consistent, maintainable screenshot and diagram usage across all SyncoPaid documentation.

**Approach:** Create `docs/visual-aids-strategy.md` that identifies key screenshots needed, defines annotation standards, plans for a workflow diagram, establishes naming/storage conventions, and plans for maintenance. Since this is a strategy document (not actual screenshots), TDD uses file existence and content validation.

**Tech Stack:** Markdown documentation only (no code changes, no actual images yet)

---

## Story Context

**Title:** Create Visual Aids Strategy

**Description:** As a documentation maintainer, I want a visual aids strategy for SyncoPaid documentation so that screenshots and diagrams enhance comprehension without creating maintenance burden.

**Acceptance Criteria:**
- [ ] Identify key screenshots needed (system tray, export dialog, settings)
- [ ] Define annotation standards per research (3-4 max, only non-obvious)
- [ ] Create workflow diagram for time tracking → export → billing cycle
- [ ] Establish screenshot naming and storage convention
- [ ] Plan for screenshot updates when UI changes
- [ ] Mark all screenshot locations in documentation with placeholders

## Prerequisites

- [ ] No code prerequisites - this is a documentation-only task
- [ ] Story 21.2 (Style Guide) provides screenshot formatting guidance (already defines "3-4 annotations max" rule)
- [ ] Familiarity with SyncoPaid's UI components: system tray icon, export dialog, main window

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `docs/visual-aids-strategy.md` | Create | Main visual aids strategy document |
| `docs/images/` | Create dir | Screenshot storage directory |
| `docs/images/.gitkeep` | Create | Preserve empty directory in git |

## Reference Material

Before writing, understand SyncoPaid UI components:

**System Tray Icon States:**
- Green stopwatch = actively tracking
- Orange stopwatch with ❚❚ = paused by user
- Faded stopwatch with 💤 = idle (paused due to inactivity)

**Key UI Elements to Document:**
- System tray icon and right-click menu
- Export dialog (date range, file location, format options)
- Main activity list window (if it exists)
- Settings/config interface (if it exists)

**Data Flow for Workflow Diagram:**
TrackerLoop polls window → ActivityEvent on change → SQLite storage → ScreenshotWorker captures → Exporter outputs JSON → User imports to billing software

---

## TDD Tasks

### Task 1: Create docs/images directory and strategy file skeleton (~3 min)

**Files:**
- Create: `docs/images/` directory
- Create: `docs/images/.gitkeep`
- Create: `docs/visual-aids-strategy.md`

**Step 1 - RED:** Verify files do not exist

Run: `ls docs/images/ 2>/dev/null || echo "DIR_NOT_FOUND"`
Expected: DIR_NOT_FOUND

Run: `ls docs/visual-aids-strategy.md 2>/dev/null || echo "FILE_NOT_FOUND"`
Expected: FILE_NOT_FOUND

**Step 2 - Implementation:**

Create the directory and strategy document header:

```bash
mkdir -p docs/images
touch docs/images/.gitkeep
```

Create `docs/visual-aids-strategy.md`:

```markdown
# Visual Aids Strategy

Guidelines for screenshots and diagrams in SyncoPaid documentation.

---

## Purpose

Visual aids help lawyers understand SyncoPaid quickly without reading long explanations. However, screenshots require maintenance when the UI changes. This strategy balances visual clarity with maintenance effort.

**Principles:**
- Screenshots for UI elements that are hard to describe in words
- Diagrams for workflows and conceptual understanding
- Text-only when the action is obvious (e.g., "Click Save")
- Update visuals only when the UI materially changes

---
```

**Step 3 - Verify GREEN:** Files exist

Run: `ls docs/images/.gitkeep && head -10 docs/visual-aids-strategy.md`
Expected: .gitkeep exists, document starts with "# Visual Aids Strategy"

**Step 4 - COMMIT:**

```bash
git add docs/images/.gitkeep docs/visual-aids-strategy.md && git commit -m "docs(21.6): create visual aids strategy skeleton and images directory"
```

---

### Task 2: Define key screenshots needed (~4 min)

**Files:**
- Modify: `docs/visual-aids-strategy.md`

**Step 1 - Implementation:**

Append to visual-aids-strategy.md:

```markdown
## Required Screenshots

These screenshots are essential for user understanding:

### Priority 1: System Tray (Critical Path)

| Screenshot | Filename | Shows | Used In |
|------------|----------|-------|---------|
| Tray icon - active | `tray-active.png` | Green stopwatch icon in system tray | Getting started, troubleshooting |
| Tray icon - paused | `tray-paused.png` | Orange icon with ❚❚ symbol | How-to: pause tracking |
| Tray icon - idle | `tray-idle.png` | Faded icon with 💤 symbol | Troubleshooting |
| Tray menu | `tray-menu.png` | Right-click context menu options | Getting started, all how-to guides |
| Hidden icons area | `tray-overflow.png` | The ^ arrow showing hidden icons | Troubleshooting: icon missing |

### Priority 2: Export Workflow (Core Feature)

| Screenshot | Filename | Shows | Used In |
|------------|----------|-------|---------|
| Export dialog | `export-dialog.png` | Full export dialog with options | How-to: export data |
| Date range picker | `export-date-range.png` | Date selection interface | How-to: export data |
| Export success | `export-success.png` | Confirmation message | How-to: export data |

### Priority 3: Activity Review (Secondary)

| Screenshot | Filename | Shows | Used In |
|------------|----------|-------|---------|
| Activity list | `activity-list.png` | Main window with tracked activities | Getting started |
| Activity details | `activity-detail.png` | Expanded view of single activity | How-to: review activities |

### Priority 4: Settings (Reference Only)

| Screenshot | Filename | Shows | Used In |
|------------|----------|-------|---------|
| Settings dialog | `settings-dialog.png` | Configuration options | Configuration reference |
| Screenshot settings | `settings-screenshots.png` | Screenshot interval option | FAQ |

---
```

**Step 2 - Verify GREEN:** Screenshot table exists

Run: `grep -c "tray-active.png" docs/visual-aids-strategy.md`
Expected: 1

**Step 3 - COMMIT:**

```bash
git add docs/visual-aids-strategy.md && git commit -m "docs(21.6): define key screenshots with priorities and filenames"
```

---

### Task 3: Define annotation standards (~4 min)

**Files:**
- Modify: `docs/visual-aids-strategy.md`

**Step 1 - Implementation:**

Append to visual-aids-strategy.md:

```markdown
## Annotation Standards

Follow the style guide rule: **3-4 annotations maximum per screenshot**.

### When to Annotate

**Do annotate:**
- Non-obvious UI elements (hidden overflow area)
- Elements with similar appearance (different tray icon states)
- Specific button/field the user needs to interact with
- Warning or caution areas

**Don't annotate:**
- Obvious elements (close button, window title)
- Elements already described in text
- Decorative elements

### Annotation Types

| Type | Use For | Style |
|------|---------|-------|
| Numbered callout | Sequential steps | Circle with number (1, 2, 3) |
| Arrow | Drawing attention | Red arrow, 3px width |
| Highlight box | Emphasizing an area | Red rectangle, no fill, 2px border |
| Text label | Naming elements | Red text, white background |

### Color Standards

- **Primary callout color:** Red (#FF0000)
- **Secondary color:** Yellow (#FFFF00) for warnings
- **Text background:** White with 80% opacity

### Examples

**Good annotation:**
```
[Screenshot of tray with one red arrow pointing to the SyncoPaid icon]
Caption: "Look for the stopwatch icon in your system tray"
```

**Bad annotation:**
```
[Screenshot with 6 different callouts pointing to every menu item]
Caption: "The system tray shows various options"
```

---
```

**Step 2 - Verify GREEN:** Annotation section exists

Run: `grep -c "3-4 annotations maximum" docs/visual-aids-strategy.md`
Expected: 1

**Step 3 - COMMIT:**

```bash
git add docs/visual-aids-strategy.md && git commit -m "docs(21.6): define annotation standards with examples"
```

---

### Task 4: Create workflow diagram specification (~5 min)

**Files:**
- Modify: `docs/visual-aids-strategy.md`

**Step 1 - Implementation:**

Append to visual-aids-strategy.md:

```markdown
## Workflow Diagram

A single diagram showing the complete time tracking → billing cycle.

### Diagram Specification

**Filename:** `workflow-diagram.png` (or `.svg` for scalability)

**Purpose:** Show lawyers the big picture of how SyncoPaid fits into their billing workflow.

**Format:** Horizontal flowchart, left-to-right reading order.

**Elements:**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   You Work      │────▶│ SyncoPaid       │────▶│  Review         │
│   (Foreground)  │     │  Tracks         │     │  Activities     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Billing        │◀────│  Categorize     │◀────│   Export        │
│  Software       │     │  (LLM/Manual)   │     │   JSON          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Labels:**
1. "You Work" - Your normal computer use
2. "SyncoPaid Tracks" - Automatic window monitoring
3. "Review Activities" - Check what was captured
4. "Export JSON" - Generate billing data
5. "Categorize" - Assign client/matter codes
6. "Billing Software" - Import for invoicing

**Style:**
- Clean, minimal boxes
- Arrows showing flow direction
- SyncoPaid logo/icon on the tracking step
- No technical jargon in labels

### When to Show This Diagram

- Getting started guide (introduction)
- FAQ: "How does SyncoPaid work?"
- Landing page / README (if applicable)

---
```

**Step 2 - Verify GREEN:** Workflow diagram section exists

Run: `grep -c "workflow-diagram.png" docs/visual-aids-strategy.md`
Expected: 1

**Step 3 - COMMIT:**

```bash
git add docs/visual-aids-strategy.md && git commit -m "docs(21.6): add workflow diagram specification with ASCII preview"
```

---

### Task 5: Establish naming and storage conventions (~3 min)

**Files:**
- Modify: `docs/visual-aids-strategy.md`

**Step 1 - Implementation:**

Append to visual-aids-strategy.md:

```markdown
## Naming Conventions

### Screenshot Filenames

Pattern: `[feature]-[element]-[state].png`

Examples:
- `tray-icon-active.png` ✓
- `tray-menu.png` ✓
- `export-dialog-daterange.png` ✓
- `screenshot1.png` ✗ (non-descriptive)
- `System Tray Menu.png` ✗ (spaces, capitals)

**Rules:**
- All lowercase
- Hyphens between words (not underscores)
- No spaces
- Descriptive but concise
- Include state suffix when relevant (active, paused, error)

### Directory Structure

```
docs/
├── images/
│   ├── tray/
│   │   ├── tray-icon-active.png
│   │   ├── tray-icon-paused.png
│   │   ├── tray-icon-idle.png
│   │   └── tray-menu.png
│   ├── export/
│   │   ├── export-dialog.png
│   │   └── export-success.png
│   ├── activity/
│   │   └── activity-list.png
│   └── diagrams/
│       └── workflow-diagram.svg
├── getting-started.md
├── troubleshooting.md
└── visual-aids-strategy.md
```

**Note:** Subdirectories are optional. For a small documentation set, a flat `images/` directory may be simpler to maintain.

---
```

**Step 2 - Verify GREEN:** Naming convention section exists

Run: `grep -c "Naming Conventions" docs/visual-aids-strategy.md`
Expected: 1

**Step 3 - COMMIT:**

```bash
git add docs/visual-aids-strategy.md && git commit -m "docs(21.6): add naming and storage conventions"
```

---

### Task 6: Plan for screenshot updates and placeholders (~4 min)

**Files:**
- Modify: `docs/visual-aids-strategy.md`

**Step 1 - Implementation:**

Append to visual-aids-strategy.md:

```markdown
## Maintenance Plan

### When to Update Screenshots

**Must update:**
- UI layout materially changed (buttons moved, new sections)
- Icon appearance changed
- Dialog options added/removed
- Branding/color scheme changed

**Can skip update:**
- Minor text changes (same structure)
- Backend changes (no visible UI impact)
- New features (add new screenshots, don't update existing)

### Update Checklist

When updating screenshots:

1. [ ] Take new screenshot at same resolution (1920x1080 recommended)
2. [ ] Apply same annotation style (colors, callout types)
3. [ ] Save with same filename (overwrites old version)
4. [ ] Verify all documentation still makes sense with new image
5. [ ] Commit with message: `docs: update [screenshot-name] for [UI change]`

### Version Tracking

Consider adding a version suffix if major UI redesign:
- `tray-menu-v1.png` (original UI)
- `tray-menu-v2.png` (redesigned UI)

Only use version suffixes for archival purposes. Active documentation should reference versionless filenames.

---

## Placeholder Markup

Until screenshots are captured, use this placeholder format in documentation:

```markdown
![System tray menu](images/tray-menu.png)
<!-- TODO-SCREENSHOT: Capture system tray right-click menu showing:
     - Start/Pause Tracking
     - Export Activities
     - Open SyncoPaid
     - Quit
     Resolution: 400x300 (cropped to menu)
     Annotations: None needed (menu items are self-explanatory)
-->
```

### Current Placeholders Needed

Review these documents and add placeholders:

| Document | Placeholder Location | Screenshot Needed |
|----------|---------------------|-------------------|
| `getting-started.md` | After "System tray icon" section | `tray-menu.png` |
| `getting-started.md` | After "Your first export" section | `export-dialog.png` |
| `troubleshooting.md` | "Icon missing" section | `tray-overflow.png` |
| `how-to/export-data.md` | Step 2 | `export-dialog.png` |
| `how-to/pause-tracking.md` | Step 1 | `tray-menu.png` |

---

## Tools and Resources

### Screenshot Capture

**Windows Snipping Tool** (built-in):
- `Win + Shift + S` for selection
- Good for quick captures

**ShareX** (recommended for annotations):
- Free, open source
- Built-in annotation tools
- Consistent styling

### Diagram Creation

**draw.io / diagrams.net** (recommended):
- Free, no account required
- Export to SVG for scalability
- Export to PNG for compatibility

**Mermaid** (alternative for version control):
- Text-based diagrams in markdown
- Renders in GitHub/GitLab

---

*Last updated: 2025-12-24*
```

**Step 2 - Verify GREEN:** Maintenance section and placeholders exist

Run: `grep -c "Maintenance Plan" docs/visual-aids-strategy.md && grep -c "TODO-SCREENSHOT" docs/visual-aids-strategy.md`
Expected: 1 and 1

**Step 3 - COMMIT:**

```bash
git add docs/visual-aids-strategy.md && git commit -m "docs(21.6): add maintenance plan and placeholder markup format"
```

---

## Final Verification

Run after all tasks complete:

```bash
# Verify files exist
ls -la docs/visual-aids-strategy.md docs/images/.gitkeep

# Count major sections (should be 7+)
grep -c "^## " docs/visual-aids-strategy.md

# Verify key sections present
grep -l "Required Screenshots" docs/visual-aids-strategy.md
grep -l "Annotation Standards" docs/visual-aids-strategy.md
grep -l "Workflow Diagram" docs/visual-aids-strategy.md
grep -l "Naming Conventions" docs/visual-aids-strategy.md
grep -l "Maintenance Plan" docs/visual-aids-strategy.md

# Verify screenshot table has entries
grep -c "\.png" docs/visual-aids-strategy.md
```

Expected output:
- Both files exist
- 7+ major sections
- All key section headings present
- 10+ .png references (in the screenshot tables)

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

**Dependencies:**
- Story 21.2 (Style Guide) should exist for annotation standards reference
- Story 21.3-21.5 (Getting Started, How-To, Troubleshooting) should add the actual placeholders listed here
- Actual screenshot capture is a future task (not part of this story)

**Design Decisions:**
- Used PNG format for screenshots (universal compatibility)
- Recommended SVG for diagrams (scalability)
- Chose red (#FF0000) for annotations (high visibility, industry standard)
- Created subdirectory structure for organization but noted flat structure is acceptable

**Future Enhancements:**
- Add automated screenshot capture with Puppeteer/Playwright (if web UI)
- Add CI check for broken image references
- Consider screenshot diffing for detecting stale images
