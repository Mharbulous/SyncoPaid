# Create SyncoPaid Documentation Style Guide - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.2 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a comprehensive documentation style guide that ensures consistent voice, terminology, and formatting across all SyncoPaid user documentation.

**Approach:** Create a Markdown style guide in `docs/` that defines the target audience persona, establishes a terminology glossary, sets formatting standards, and provides examples of good vs bad writing for lawyers using time-tracking software.

**Tech Stack:** Markdown documentation only (no code changes)

---

## Story Context

**Title:** Create SyncoPaid Documentation Style Guide

**Description:** As a documentation maintainer, I want a project-specific style guide for SyncoPaid documentation so that all manual content maintains consistent voice, terminology, and formatting as it grows.

**Acceptance Criteria:**
- [ ] Define target audience persona (lawyer using time tracking for billing)
- [ ] Establish terminology glossary (e.g., "activity" vs "event", "window" vs "application")
- [ ] Set language calibration (accessible for legal professionals, avoid developer jargon)
- [ ] Define formatting standards (heading hierarchy, list styles, callout types)
- [ ] Create boilerplate patterns for common elements (steps, warnings, tips)
- [ ] Store style guide in docs/ for reference during generation
- [ ] Include examples of good vs bad writing for this audience

## Prerequisites

- [ ] No code prerequisites - this is a documentation-only task
- [ ] Familiarity with SyncoPaid's purpose: automatic time tracking for lawyers

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `docs/STYLE-GUIDE.md` | Create | Main style guide for all documentation |
| `docs/` | Create dir | Documentation directory |

## Reference Material

Before writing, understand SyncoPaid context:

- **Product purpose:** Automatic time-tracking for lawyers, captures window activities, exports JSON for LLM billing categorization
- **Key terminology from codebase:**
  - `ActivityEvent` - a tracked window activity with timestamp, duration, app, title
  - `TrackerLoop` - the component that monitors active windows
  - `ScreenshotWorker` - captures screenshots for context
  - `Exporter` - exports data to JSON
  - States: Active, Inactive, Off, Blocked, Paused, Personal, On-break
  - Client matter pattern: `1023.L213` format (4 digits, dot, optional letter, 3 digits)
- **User data location:** `%LOCALAPPDATA%\SyncoPaid\`

## TDD Tasks

### Task 1: Create docs directory and style guide skeleton (~3 min)

**Files:**
- Create: `docs/` directory
- Create: `docs/STYLE-GUIDE.md`

**Context:** This task establishes the directory structure and main document. The style guide will be the foundational reference for all user-facing documentation.

**Step 1:** Create directory and file
```bash
mkdir -p docs
```

**Step 2:** Create style guide with header and audience section
```markdown
# SyncoPaid Documentation Style Guide

This guide ensures consistency across all SyncoPaid user documentation.

---

## Target Audience

**Primary Persona:** Legal professional (lawyer, paralegal) who:
- Needs to track billable hours across multiple client matters
- Is comfortable with Windows desktop applications
- May not have technical background (avoid developer jargon)
- Values efficiency and accuracy in billing records
- Is frustrated by manual time entry

**Reading Context:**
- Often scanning quickly for specific information
- May be reading while under time pressure
- Needs immediate, actionable guidance
- Prefers concrete examples over abstract explanations

**Writing Calibration:**
- Write for someone who knows their legal work, not software development
- Assume basic Windows proficiency (can use system tray, file explorer)
- Explain any technical terms when first used
- Keep sentences concise and active
```

**Step 3 - Verify:** File exists with audience section
```bash
cat docs/STYLE-GUIDE.md | head -30
```
Expected output: Shows the header and Target Audience section

**Step 4 - COMMIT:**
```bash
git add docs/STYLE-GUIDE.md && git commit -m "docs: create style guide with target audience persona"
```

---

### Task 2: Add terminology glossary (~4 min)

**Files:**
- Modify: `docs/STYLE-GUIDE.md`

**Context:** Establishes consistent terminology between developer concepts and user-facing language. This prevents confusion from inconsistent terms.

**Step 1:** Append terminology section to style guide
```markdown

---

## Terminology Glossary

Use these terms consistently across all documentation:

| User-Facing Term | Internal/Code Term | Definition |
|------------------|-------------------|------------|
| **activity** | `ActivityEvent` | A single tracked window session with start time and duration |
| **application** | `app` | The software program (e.g., "Microsoft Word", "Chrome") |
| **window title** | `title` | The text shown in the window's title bar |
| **tracking** | `TrackerLoop` | The background monitoring of your active windows |
| **screenshot** | `screenshot` | Periodic screen capture for review context |
| **export** | `Exporter` | Saving your activity data as a JSON file |
| **system tray** | tray icon | The small SyncoPaid icon near the clock |
| **matter number** | client matter | Billing code like "1023.L213" |
| **idle** | `Inactive` state | When you're away from the computer |
| **paused** | `Paused` state | When you've manually stopped tracking |

### Terms to Avoid

| Instead of... | Use... | Reason |
|---------------|--------|--------|
| "event" | "activity" | Less technical |
| "poll" | "check" or "monitor" | Developer jargon |
| "config" | "settings" | User-friendly |
| "JSON" (alone) | "JSON file" or "data file" | Clarifies it's a file |
| "dHash" | "duplicate detection" | Too technical |
| "database" | "stored data" or "records" | Simpler |
```

**Step 2 - Verify:** Glossary section exists
```bash
grep -c "Terminology Glossary" docs/STYLE-GUIDE.md
```
Expected output: `1`

**Step 3 - COMMIT:**
```bash
git add docs/STYLE-GUIDE.md && git commit -m "docs: add terminology glossary to style guide"
```

---

### Task 3: Add formatting standards (~4 min)

**Files:**
- Modify: `docs/STYLE-GUIDE.md`

**Context:** Defines the visual structure and hierarchy for documentation. Consistent formatting helps users navigate quickly.

**Step 1:** Append formatting section to style guide
```markdown

---

## Formatting Standards

### Heading Hierarchy

```
# Document Title (one per file)
## Major Section (key topics)
### Subsection (supporting details)
#### Rarely Used (only for complex hierarchies)
```

### Lists

**Use numbered lists for:**
- Sequential steps (do this, then that)
- Ranked items (most to least important)

**Use bullet lists for:**
- Unordered items
- Features, options, examples

**List formatting:**
- Start each item with a capital letter
- No periods for short items (under 10 words)
- Periods for complete sentences

### Callout Types

Use these callout patterns consistently:

**Tip (helpful but optional):**
> **Tip:** You can right-click the system tray icon for quick access to export.

**Note (important context):**
> **Note:** SyncoPaid only tracks activities while running.

**Warning (potential issues):**
> **Warning:** Exporting large date ranges may take several seconds.

**Caution (data loss risk):**
> **Caution:** Deleted activities cannot be recovered.

### Code and Paths

- File paths: Use code formatting: `C:\Users\...\SyncoPaid\`
- Settings values: Use code formatting: `screenshot_interval_seconds`
- User input: Use bold: Type **your matter number**
- Button/menu names: Use bold: Click **Export**

### Screenshots

- Maximum 3-4 annotations per screenshot
- Only annotate non-obvious elements
- Use arrows for focus, circles for emphasis
- Include alt text for accessibility
```

**Step 2 - Verify:** Formatting section exists
```bash
grep -c "Formatting Standards" docs/STYLE-GUIDE.md
```
Expected output: `1`

**Step 3 - COMMIT:**
```bash
git add docs/STYLE-GUIDE.md && git commit -m "docs: add formatting standards to style guide"
```

---

### Task 4: Add writing patterns and examples (~5 min)

**Files:**
- Modify: `docs/STYLE-GUIDE.md`

**Context:** Provides concrete examples of good vs bad writing. This is the most actionable section for maintaining consistency.

**Step 1:** Append writing patterns section to style guide
```markdown

---

## Writing Patterns

### Task-Oriented Headings

Start headings with action verbs:

| Good | Bad |
|------|-----|
| Export your activities | Activity Export |
| Review tracked time | Tracked Time Review |
| Pause tracking | Tracking Pause Feature |
| Set up SyncoPaid | SyncoPaid Setup |

### Step Instructions

Write steps in active voice with clear actions:

**Good:**
1. Right-click the SyncoPaid icon in the system tray.
2. Select **Export Activities**.
3. Choose a date range.
4. Click **Save**.

**Bad:**
1. The system tray icon can be right-clicked.
2. Export Activities should be selected.
3. A date range must be chosen.
4. Save is clicked.

### Concise Explanations

Get to the point quickly:

**Good:**
> SyncoPaid tracks which windows you use and for how long. This data helps you create accurate billing records.

**Bad:**
> SyncoPaid is an application that has been designed to help users track their window activities by monitoring which windows are in the foreground at any given time, and recording the duration of time spent in each window, which can then be used for the purpose of creating billing records.

### Error Messages and Troubleshooting

Be specific and actionable:

**Good:**
> **Problem:** SyncoPaid isn't tracking my activities.
>
> **Solution:** Check that SyncoPaid is running (look for the icon in the system tray). If the icon shows "Paused", right-click and select **Resume Tracking**.

**Bad:**
> If tracking doesn't work, try restarting.

---

## Boilerplate Patterns

### Getting Started Intro
```
This guide helps you [accomplish goal] in [timeframe].
By the end, you'll have [specific outcome].
```

### Step-by-Step Template
```
## [Action Verb] [Object]

[1-2 sentence context - why you'd do this]

1. [First action with specific UI element]
2. [Second action]
3. [Third action]

> **Tip:** [Optional helpful hint]

When complete, you'll see [success indicator].
```

### Troubleshooting Entry Template
```
### [Error message or symptom]

**Cause:** [Why this happens]

**Solution:**
1. [First fix attempt]
2. [Second fix attempt if first doesn't work]

If the problem persists, [escalation path].
```
```

**Step 2 - Verify:** Writing patterns section exists with examples
```bash
grep -c "Writing Patterns" docs/STYLE-GUIDE.md && grep -c "Good" docs/STYLE-GUIDE.md
```
Expected output: `1` and a count > 3 (multiple "Good" examples)

**Step 3 - COMMIT:**
```bash
git add docs/STYLE-GUIDE.md && git commit -m "docs: add writing patterns and examples to style guide"
```

---

### Task 5: Add maintenance checklist and finalize (~3 min)

**Files:**
- Modify: `docs/STYLE-GUIDE.md`

**Context:** Provides a quick-reference checklist for documentation authors to ensure compliance with the style guide.

**Step 1:** Append checklist section to style guide
```markdown

---

## Documentation Checklist

Before publishing any documentation, verify:

### Content
- [ ] Written for lawyer audience (no unexplained technical jargon)
- [ ] Task-oriented headings (start with action verbs)
- [ ] Uses consistent terminology (check glossary)
- [ ] Includes specific UI element names (buttons, menus)
- [ ] Steps are numbered and sequential

### Formatting
- [ ] Heading hierarchy is correct (# for title, ## for sections)
- [ ] Callouts use correct patterns (Tip/Note/Warning/Caution)
- [ ] File paths and settings use code formatting
- [ ] Button/menu names are bold

### Quality
- [ ] Sentences are concise (prefer under 20 words)
- [ ] Active voice throughout
- [ ] Specific outcomes stated ("you'll see..." not "it works")
- [ ] Tested the steps personally

---

## File Locations

| Document Type | Location | Example |
|---------------|----------|---------|
| Style guide | `docs/STYLE-GUIDE.md` | This file |
| Getting started | `docs/getting-started.md` | First-run guide |
| How-to guides | `docs/how-to/` | `export-activities.md` |
| Troubleshooting | `docs/troubleshooting.md` | FAQ and fixes |
| Screenshots | `docs/images/` | `system-tray-menu.png` |

---

*Last updated: 2025-12-24*
```

**Step 2 - Verify:** Complete style guide with all sections
```bash
wc -l docs/STYLE-GUIDE.md
```
Expected output: ~200+ lines (complete document)

**Step 3 - Verify:** All acceptance criteria sections present
```bash
grep -E "(Target Audience|Terminology Glossary|Formatting Standards|Writing Patterns|Checklist)" docs/STYLE-GUIDE.md | wc -l
```
Expected output: `5` (all major sections)

**Step 4 - COMMIT:**
```bash
git add docs/STYLE-GUIDE.md && git commit -m "docs: add checklist and file locations to complete style guide"
```

---

## Final Verification

Run after all tasks complete:
```bash
# Verify file exists with expected content
ls -la docs/STYLE-GUIDE.md

# Verify all sections present
grep -E "^## " docs/STYLE-GUIDE.md

# Expected sections:
# ## Target Audience
# ## Terminology Glossary
# ## Formatting Standards
# ## Writing Patterns
# ## Documentation Checklist
# ## File Locations
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This style guide is foundational for stories 21.3-21.7 (Getting Started, How-To Guides, Troubleshooting, Visual Aids, Maintenance Workflow)
- The terminology glossary should be updated as new features are added
- Consider adding a "Version History" section as documentation grows
- Screenshots directory (`docs/images/`) can be created when visual aids story (21.6) is implemented
