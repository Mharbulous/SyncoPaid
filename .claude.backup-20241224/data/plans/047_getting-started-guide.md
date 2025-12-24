# Generate Getting Started Guide - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.3 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a Getting Started guide that enables lawyers to install SyncoPaid and verify time tracking works within 5 minutes.

**Approach:** Create `docs/getting-started.md` following the quick-start template pattern. The guide covers Windows 11 installation, system tray basics, and verification that tracking is working. Since this is documentation-only (no code changes), TDD uses validation scripts instead of unit tests.

**Tech Stack:** Markdown documentation only (no code changes)

---

## Story Context

**Title:** Generate Getting Started Guide

**Description:** As a lawyer using SyncoPaid for the first time, I want a clear getting started guide so that I can install and begin tracking time within 5 minutes.

**Acceptance Criteria:**
- [ ] Installation steps for Windows 11 (single-click or minimal steps)
- [ ] First launch experience (what to expect in system tray)
- [ ] Quick verification that tracking is working
- [ ] First meaningful task: view tracked activities
- [ ] Time-to-value under 5 minutes
- [ ] No prerequisites beyond Windows 11
- [ ] Success criteria clearly stated

## Prerequisites

- [ ] docs/ directory may not exist - create if needed
- [ ] Style guide (Story 21.2) may or may not be complete - reference if available, use sensible defaults if not

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `docs/` | Create dir | Documentation directory |
| `docs/getting-started.md` | Create | Getting started guide for new users |

## Reference Material

**SyncoPaid Context:**
- **Purpose:** Automatic time-tracking for lawyers, captures window activities, runs in system tray
- **System Tray Icons:**
  - Green stopwatch = tracking active
  - Orange stopwatch with pause icon = user paused
  - Faded stopwatch with sleep icon = idle (no activity for 5 min)
- **Data Location:** `%LOCALAPPDATA%\SyncoPaid\` (database, config, screenshots)
- **Right-click menu:** Start/Pause Tracking, Open SyncoPaid, Start with Windows, About, Quit

**Application Launch:** `python -m syncopaid` (dev mode) or double-click installer (production)

---

## TDD Tasks

### Task 1: Create docs directory and guide skeleton (~3 min)

**Files:**
- Create: `docs/` directory
- Create: `docs/getting-started.md`

**Context:** This task creates the documentation directory structure and initial Getting Started guide with proper header and introduction. The docs/ directory will hold all user documentation.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - Create directory and file:**
```bash
mkdir -p docs
```

**Step 3 - GREEN:** Create getting-started.md with introduction
```markdown
# Getting Started with SyncoPaid

Get your automatic time tracking running in under 5 minutes.

## What You'll Accomplish

By the end of this guide, you will:
- Have SyncoPaid installed and running on Windows 11
- Understand the system tray icons and what they mean
- Verify that time tracking is capturing your activities
- Know how to pause and resume tracking

## Before You Begin

**Requirements:**
- Windows 11 (Windows 10 may work but is not officially supported)
- Administrator access to install software

**Time needed:** About 5 minutes
```

**Step 4 - Verify GREEN:**
```bash
test -f docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 5 - COMMIT:**
```bash
git add docs/ && git commit -m "docs: create getting-started guide skeleton"
```

---

### Task 2: Add installation section (~3 min)

**Files:**
- Modify: `docs/getting-started.md`

**Context:** This task adds the installation instructions. Since SyncoPaid is a Windows desktop app distributed via installer, the steps should be minimal and lawyer-friendly.

**Step 1 - RED:** Verify installation section doesn't exist
```bash
grep -q "## Step 1: Install SyncoPaid" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Append installation section to file
```markdown

---

## Step 1: Install SyncoPaid

1. **Download the installer**
   - Get the latest SyncoPaid installer from your IT administrator or the download link provided

2. **Run the installer**
   - Double-click the downloaded file (e.g., `SyncoPaid-Setup.exe`)
   - If Windows SmartScreen appears, click "More info" then "Run anyway"
   - Follow the installation prompts (defaults are recommended)

3. **Launch SyncoPaid**
   - The installer will offer to start SyncoPaid automatically
   - If not, find "SyncoPaid" in your Start menu and click it

**What happens:** SyncoPaid starts silently and appears in your system tray (the small icons near your clock, bottom-right of your screen).
```

**Step 3 - Verify GREEN:**
```bash
grep -q "## Step 1: Install SyncoPaid" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/getting-started.md && git commit -m "docs: add installation section to getting-started"
```

---

### Task 3: Add system tray explanation (~3 min)

**Files:**
- Modify: `docs/getting-started.md`

**Context:** New users need to understand the system tray icons since SyncoPaid runs silently in the background. This section explains what each icon state means.

**Step 1 - RED:** Verify section doesn't exist
```bash
grep -q "## Step 2: Find SyncoPaid in Your System Tray" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Append system tray section
```markdown

---

## Step 2: Find SyncoPaid in Your System Tray

Look for the **stopwatch icon** in your system tray (bottom-right corner, near the clock).

### Understanding the Icon Colors

| Icon | Meaning |
|------|---------|
| **Green stopwatch** | Actively tracking your work |
| **Orange stopwatch** (with pause bars) | You paused tracking |
| **Faded stopwatch** (with sleep symbol) | No activity detected for 5 minutes |

**Tip:** If you don't see the icon, click the small arrow (^) in the system tray to show hidden icons.

### Right-Click Menu

Right-click the SyncoPaid icon to see your options:

- **Start/Pause Tracking** - Toggle time tracking on or off
- **Open SyncoPaid** - View your tracked activities
- **Start with Windows** - Have SyncoPaid launch automatically when you log in
- **About** - View version information
- **Quit** - Close SyncoPaid completely
```

**Step 3 - Verify GREEN:**
```bash
grep -q "## Step 2: Find SyncoPaid in Your System Tray" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/getting-started.md && git commit -m "docs: add system tray explanation to getting-started"
```

---

### Task 4: Add verification section (~3 min)

**Files:**
- Modify: `docs/getting-started.md`

**Context:** Users need to verify tracking is working. This section provides a simple test they can perform immediately.

**Step 1 - RED:** Verify section doesn't exist
```bash
grep -q "## Step 3: Verify Tracking Is Working" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Append verification section
```markdown

---

## Step 3: Verify Tracking Is Working

Let's confirm SyncoPaid is capturing your activities.

### Quick Test

1. **Open a few applications** - Switch between 2-3 programs (e.g., your web browser, Microsoft Word, and Outlook)

2. **Wait about 30 seconds** - Give SyncoPaid time to record the activity changes

3. **Check your tracked activities**
   - Right-click the SyncoPaid icon in the system tray
   - Select **Open SyncoPaid**
   - You should see your recent activities listed with timestamps

### What You Should See

Your activity list will show:
- **Application name** (e.g., "chrome.exe", "OUTLOOK.EXE")
- **Window title** (e.g., "Email - Microsoft Outlook")
- **Time spent** in each window

**Success!** If you see your recent application switches listed, SyncoPaid is tracking correctly.
```

**Step 3 - Verify GREEN:**
```bash
grep -q "## Step 3: Verify Tracking Is Working" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/getting-started.md && git commit -m "docs: add verification section to getting-started"
```

---

### Task 5: Add next steps and success message (~3 min)

**Files:**
- Modify: `docs/getting-started.md`

**Context:** Completes the guide with a success message and points users to next steps for continued learning.

**Step 1 - RED:** Verify section doesn't exist
```bash
grep -q "## You're All Set!" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Append success and next steps section
```markdown

---

## You're All Set!

**Congratulations!** SyncoPaid is now tracking your work activities automatically.

**What you've accomplished:**
- Installed SyncoPaid on Windows 11
- Located the system tray icon and understood its states
- Verified that activity tracking is working
- Learned how to view your tracked activities

### What Happens Next

SyncoPaid runs quietly in the background. Just work normally, and it will:
- Record which applications you use and when
- Track how long you spend in each window
- Capture periodic screenshots for context (optional)
- Store everything locally on your computer for privacy

### Common Tasks

| Task | How to Do It |
|------|--------------|
| Pause tracking | Right-click tray icon → "Pause Tracking" |
| Resume tracking | Right-click tray icon → "Start Tracking" |
| View activities | Right-click tray icon → "Open SyncoPaid" |
| Export for billing | See the [Exporting Data Guide](./exporting-data.md) |

### Need Help?

If something isn't working as expected, check the [Troubleshooting Guide](./troubleshooting.md).

---

*Last updated: December 2024*
```

**Step 3 - Verify GREEN:**
```bash
grep -q "## You're All Set!" docs/getting-started.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/getting-started.md && git commit -m "docs: add success message and next steps to getting-started"
```

---

## Final Verification

Run after all tasks complete:
```bash
# Verify file exists and has all sections
test -f docs/getting-started.md && echo "File exists: OK"
grep -q "## Step 1: Install SyncoPaid" docs/getting-started.md && echo "Step 1: OK"
grep -q "## Step 2: Find SyncoPaid" docs/getting-started.md && echo "Step 2: OK"
grep -q "## Step 3: Verify Tracking" docs/getting-started.md && echo "Step 3: OK"
grep -q "## You're All Set!" docs/getting-started.md && echo "Conclusion: OK"

# Verify word count is reasonable (should be 400-800 words for 5-min read)
wc -w docs/getting-started.md
```

Expected: All "OK" messages, word count around 500-700

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- Referenced guides (exporting-data.md, troubleshooting.md) are placeholders for future stories (21.4, 21.5)
- Screenshots/diagrams mentioned in parent story 21 can be added in Story 21.6 (Visual Aids Strategy)
- If Style Guide (21.2) is complete, review docs/STYLE-GUIDE.md before executing this plan to ensure consistency
