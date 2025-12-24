# Generate Troubleshooting Section - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.5 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a troubleshooting section that enables lawyers to resolve common SyncoPaid issues without technical support.

**Approach:** Create `docs/troubleshooting.md` following the troubleshooting template pattern. Each problem includes plain-language explanation, diagnostic steps, and resolution guide. Uses progressive disclosure (summary first, expandable details). Since this is documentation-only, TDD uses file existence and content validation.

**Tech Stack:** Markdown documentation only (no code changes)

---

## Story Context

**Title:** Generate Troubleshooting Section

**Description:** As a lawyer encountering issues with SyncoPaid, I want a troubleshooting section with common problems and solutions so that I can resolve issues without technical support.

**Acceptance Criteria:**
- [ ] Common error messages with plain-language explanations
- [ ] "SyncoPaid isn't tracking" diagnostic steps
- [ ] "Export isn't working" resolution guide
- [ ] "System tray icon missing" recovery steps
- [ ] FAQ section with 10+ questions
- [ ] Each problem links to relevant how-to guides
- [ ] Uses progressive disclosure (summary first, details expandable)

## Prerequisites

- [ ] No code prerequisites - this is a documentation-only task
- [ ] Familiarity with SyncoPaid's purpose: automatic time tracking for lawyers
- [ ] Familiarity with Windows 11 system tray behavior

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `docs/troubleshooting.md` | Create | Main troubleshooting guide |
| `docs/` | Ensure exists | Documentation directory |

## Reference Material

Before writing, understand SyncoPaid context:
- Database: `%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db` (SQLite)
- Config: `%LOCALAPPDATA%\SyncoPaid\config.json`
- Screenshots: `%LOCALAPPDATA%\SyncoPaid\screenshots\YYYY-MM-DD\`
- System tray: Uses pystray library
- Tracker: Polls active window every 1 second
- Export: JSON format with date filtering

---

## TDD Tasks

### Task 1: Create docs directory and troubleshooting file (~3 min)

**Files:**
- Create: `docs/troubleshooting.md`

**Step 1 - RED:** Verify file does not exist

Run: `ls docs/troubleshooting.md 2>/dev/null || echo "FILE_NOT_FOUND"`
Expected: FILE_NOT_FOUND

**Step 2 - Implementation:**

Create the troubleshooting header and quick diagnostic section:

```markdown
# Troubleshooting

Solutions to common problems with SyncoPaid.

## Quick Diagnostic

Before diving into specific errors, try these general troubleshooting steps:

1. **Check if SyncoPaid is running**: Look for the stopwatch icon in your system tray (bottom-right corner of screen, near the clock)

2. **Verify tracking status**:
   - Green stopwatch = actively tracking
   - Orange stopwatch with ❚❚ = paused by you
   - Faded stopwatch with 💤 = paused due to inactivity (will resume when you start working)

3. **View recent activity**: Right-click the tray icon → "Open SyncoPaid" → check if recent windows are listed

4. **Check the log file**: Open `%LOCALAPPDATA%\SyncoPaid\syncopaid.log` in Notepad to see recent error messages

If these don't help, see specific problems below.

---
```

**Step 3 - Verify GREEN:** File exists with header

Run: `head -20 docs/troubleshooting.md`
Expected: Content starts with "# Troubleshooting"

**Step 4 - COMMIT:**

```bash
mkdir -p docs && git add docs/troubleshooting.md && git commit -m "docs(21.5): create troubleshooting section with quick diagnostic"
```

---

### Task 2: Add "SyncoPaid isn't tracking" section (~5 min)

**Files:**
- Modify: `docs/troubleshooting.md`

**Step 1 - Implementation:**

Append to troubleshooting.md:

```markdown
## Common Problems

### SyncoPaid isn't tracking my work

**Symptoms**: Time entries are missing, tray icon shows but activities aren't recorded

**Quick check**: Is the icon green? If not, that's your first clue.

<details>
<summary><strong>📋 Diagnostic Steps</strong></summary>

1. **Check tray icon color**:
   - **Orange with ❚❚**: You paused tracking. Right-click → "Start Tracking" to resume.
   - **Faded with 💤**: You were away. Start using your computer and tracking resumes automatically.
   - **Green but no entries**: The problem is elsewhere—continue below.

2. **Verify SyncoPaid is actually running**:
   - Press `Ctrl+Shift+Esc` to open Task Manager
   - Look for "python" or "SyncoPaid" in the list
   - If not found, restart SyncoPaid from Start Menu

3. **Check if Windows changed the application name**:
   - Some applications (like browsers) change window titles frequently
   - SyncoPaid groups activities by window title—check if entries are under a different name

4. **Verify database permissions**:
   - Open File Explorer
   - Navigate to `%LOCALAPPDATA%\SyncoPaid\`
   - Right-click `SyncoPaid.db` → Properties → Security
   - Ensure your user has "Full control"

</details>

**Still not working?** See [Reinstalling SyncoPaid](#reinstalling-syncopaid) below.

---

### Export isn't working

**Symptoms**: Export button does nothing, export file is empty, or JSON file can't be opened

<details>
<summary><strong>📋 Resolution Steps</strong></summary>

1. **Check date range**:
   - Make sure your selected date range contains tracked activities
   - Try expanding the range to "Last 7 days" or "Last 30 days"

2. **Verify export location**:
   - By default, exports go to your Documents folder
   - Check if you have write permissions there
   - Try exporting to Desktop instead

3. **Check for special characters**:
   - If export filename contains special characters, try a simple name like "export.json"

4. **Open JSON in correct application**:
   - JSON files are text files—double-clicking may open a code editor
   - For viewing, open with Notepad or a JSON viewer
   - For billing import, your billing software handles the format

5. **Check file size**:
   - If export is 0 KB, no activities matched your date range
   - Expand date range or check that tracking was running during that period

</details>

**Need to interpret the export?** See [How to interpret exported JSON](./how-to/interpret-json-export.md).

---
```

**Step 2 - Verify GREEN:** Content includes tracking section

Run: `grep -c "isn't tracking" docs/troubleshooting.md`
Expected: 1 (or more)

**Step 3 - COMMIT:**

```bash
git add docs/troubleshooting.md && git commit -m "docs(21.5): add tracking and export troubleshooting sections"
```

---

### Task 3: Add "System tray icon missing" section (~4 min)

**Files:**
- Modify: `docs/troubleshooting.md`

**Step 1 - Implementation:**

Append to troubleshooting.md:

```markdown
### System tray icon missing

**Symptoms**: SyncoPaid was running but you can't see the icon in your system tray

<details>
<summary><strong>📋 Recovery Steps</strong></summary>

1. **Check hidden icons**:
   - Click the `^` arrow in your system tray (near the clock)
   - SyncoPaid icon may be in the overflow area
   - Drag it to the main tray area so it's always visible

2. **Windows 11 specific**: Check system tray settings:
   - Right-click taskbar → "Taskbar settings"
   - Scroll to "Other system tray icons"
   - Find "SyncoPaid" or "python" and toggle it **On**

3. **Check if SyncoPaid is running**:
   - Press `Ctrl+Shift+Esc` for Task Manager
   - Look for "python" or "SyncoPaid"
   - If running but no icon, restart SyncoPaid

4. **Restart SyncoPaid**:
   - If found in Task Manager, right-click → End task
   - Start SyncoPaid again from Start Menu
   - Watch for icon to appear in tray

5. **Restart Windows Explorer** (advanced):
   - Open Task Manager (`Ctrl+Shift+Esc`)
   - Find "Windows Explorer"
   - Right-click → Restart
   - This refreshes the system tray without restarting your computer

</details>

**Icon disappeared after Windows update?** Windows updates sometimes reset tray icon visibility. Follow step 2 above.

---

### SyncoPaid won't start

**Symptoms**: Double-clicking does nothing, or you see an error message

<details>
<summary><strong>📋 Diagnostic Steps</strong></summary>

1. **Check error message**:
   - If you see "Python not found" or "DLL error", see [Installation Issues](#installation-issues)
   - If you see "Another instance is running", SyncoPaid is already open (check system tray)

2. **Check the log file**:
   - Open `%LOCALAPPDATA%\SyncoPaid\syncopaid.log`
   - Look for recent error messages (scroll to bottom)
   - Common errors:
     - "Database locked" → another process is using the database
     - "Permission denied" → file permission issue
     - "Module not found" → reinstallation needed

3. **Try running from command line**:
   - Open Command Prompt
   - Type: `python -m syncopaid`
   - Watch for error messages that explain the problem

4. **Check antivirus**:
   - Some antivirus software blocks Python applications
   - Add SyncoPaid folder to exclusions: `%LOCALAPPDATA%\SyncoPaid\`

</details>

**Need to reinstall?** See [Reinstalling SyncoPaid](#reinstalling-syncopaid) below.

---
```

**Step 2 - Verify GREEN:** Content includes tray icon section

Run: `grep -c "tray icon missing" docs/troubleshooting.md`
Expected: 1

**Step 3 - COMMIT:**

```bash
git add docs/troubleshooting.md && git commit -m "docs(21.5): add tray icon and startup troubleshooting sections"
```

---

### Task 4: Add FAQ section (~5 min)

**Files:**
- Modify: `docs/troubleshooting.md`

**Step 1 - Implementation:**

Append to troubleshooting.md:

```markdown
## Frequently Asked Questions

### General

**Q: Does SyncoPaid track what I type?**

No. SyncoPaid only records:
- Application names (e.g., "Microsoft Word")
- Window titles (e.g., "Document1.docx - Word")
- Time spent in each window
- Optional screenshots for your reference

It does not capture keystrokes, passwords, or any text you type.

---

**Q: Does SyncoPaid send my data anywhere?**

No. All data stays on your computer in `%LOCALAPPDATA%\SyncoPaid\`. Nothing is uploaded to the internet. You control when and how to export your data.

---

**Q: How much disk space does SyncoPaid use?**

- Database: Usually under 50 MB, even after months of use
- Screenshots: Approximately 50-100 KB each, stored in daily folders
- You can configure screenshot retention in settings

---

**Q: Can I track time on multiple monitors?**

Yes. SyncoPaid tracks the active window regardless of which monitor it's on. If you switch between monitors while in the same application, it's recorded as continuous time in that application.

---

### Tracking

**Q: Why are some activities grouped together?**

SyncoPaid groups activities by window title. If you work in multiple browser tabs, each tab with a different title is recorded separately. This helps distinguish between different tasks in the same application.

---

**Q: Can I edit tracked time entries?**

Currently, SyncoPaid records activities automatically. Manual editing is not available in the current version. You can export data and adjust entries in your billing software.

---

**Q: What happens when I lock my screen?**

When you lock your screen or step away:
1. SyncoPaid detects no keyboard/mouse activity
2. After 5 minutes, the icon turns faded with 💤
3. Time is not counted during this inactive period
4. When you return, tracking resumes automatically

---

**Q: Can I pause tracking for personal activities?**

Yes. Right-click the tray icon → "Pause Tracking". The icon turns orange with ❚❚. Click "Start Tracking" to resume. Personal time is not recorded while paused.

---

### Export and Billing

**Q: What format is the export file?**

JSON (JavaScript Object Notation). This is a standard data format that most billing software can import. If your billing software doesn't accept JSON, you can open it in Excel or convert it with free online tools.

---

**Q: Can I export for specific clients or matters?**

Yes. When exporting, you can filter by:
- Date range
- Application
- Client/matter (if you've categorized your activities)

See [How to export activity data](./how-to/export-data.md) for step-by-step instructions.

---

**Q: Why is my exported time different from what I expected?**

Common reasons:
- Idle time is excluded (when you were away from computer)
- Paused periods are excluded (when you manually paused)
- Very brief window switches (under 1 second) may not be recorded
- Check your date range includes all expected days

---

### Configuration

**Q: Can I change how often screenshots are taken?**

Yes. Edit `%LOCALAPPDATA%\SyncoPaid\config.json`:
```json
{
  "screenshot_interval_seconds": 30
}
```
Default is 10 seconds. Set higher for fewer screenshots. Set to 0 to disable screenshots entirely.

---

**Q: Can I exclude certain applications from tracking?**

This feature is planned for a future update. Currently, all active windows are tracked. You can filter when exporting.

---

**Q: Where is my configuration file?**

`%LOCALAPPDATA%\SyncoPaid\config.json`

To open: Press `Win+R`, paste the path, press Enter.

---

## Installation Issues

### Reinstalling SyncoPaid

If SyncoPaid has persistent problems, a clean reinstall often helps:

1. **Backup your data** (optional but recommended):
   - Copy `%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db` to a safe location
   - This contains all your tracked activities

2. **Close SyncoPaid**:
   - Right-click tray icon → Quit
   - Or use Task Manager to end the process

3. **Delete the SyncoPaid folder**:
   - Navigate to `%LOCALAPPDATA%\`
   - Delete the `SyncoPaid` folder
   - This removes all settings and cached data

4. **Reinstall SyncoPaid**:
   - Run the installer again
   - Start SyncoPaid from Start Menu

5. **Restore your data** (if backed up):
   - Copy your backed-up `SyncoPaid.db` to the new `%LOCALAPPDATA%\SyncoPaid\` folder

### Python-related errors

If you see errors mentioning Python, pip, or missing modules:

1. **Verify Python installation**:
   - Open Command Prompt
   - Type: `python --version`
   - Should show Python 3.11 or higher

2. **Reinstall dependencies**:
   ```
   pip install pywin32 psutil pystray Pillow imagehash
   ```

3. **If Python isn't found**, reinstall Python from [python.org](https://www.python.org/) and ensure "Add to PATH" is checked during installation.

---

## Getting More Help

If you've tried the solutions above and still need help:

1. **Check the log file** at `%LOCALAPPDATA%\SyncoPaid\syncopaid.log` for specific error messages

2. **Note your SyncoPaid version** (visible in About dialog)

3. **Describe what you were doing** when the problem occurred

4. **Report issues** at https://github.com/Mharbulous/SyncoPaid/issues

---

*Last updated: 2025-12-24*
```

**Step 2 - Verify GREEN:** FAQ section has 10+ questions

Run: `grep -c "^\\*\\*Q:" docs/troubleshooting.md`
Expected: 13 (or more)

**Step 3 - COMMIT:**

```bash
git add docs/troubleshooting.md && git commit -m "docs(21.5): add FAQ section with 13 questions"
```

---

## Final Verification

Run after all tasks complete:

```bash
# Verify file exists
ls -la docs/troubleshooting.md

# Count FAQ questions (should be 10+)
grep -c "^\*\*Q:" docs/troubleshooting.md

# Verify key sections exist
grep -l "isn't tracking" docs/troubleshooting.md
grep -l "Export isn't working" docs/troubleshooting.md
grep -l "tray icon missing" docs/troubleshooting.md
grep -l "Frequently Asked Questions" docs/troubleshooting.md

# Check links work (should reference other docs)
grep -o "\\./how-to/[a-z-]*\\.md" docs/troubleshooting.md
```

Expected output:
- File exists with reasonable size
- 13+ FAQ questions
- All key sections present
- Links to how-to guides present

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

**Dependencies:**
- Story 21.4 (Core Task How-To Guides) should be complete for cross-links to work
- Until then, the links to how-to guides will be broken (acceptable)

**Style Decisions:**
- Used `<details>` tags for progressive disclosure (summary visible, details expandable)
- FAQ uses bold Q: format for scannability
- All paths use Windows format (`%LOCALAPPDATA%\`) per target platform
- Avoided technical jargon; used plain language for lawyers

**Future Enhancements:**
- Add screenshots showing tray icon states
- Add video walkthrough for common issues
- Integrate with help system in application
