# Generate Core Task How-To Guides - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.4 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create 5 single-task how-to guides enabling lawyers to accomplish common billing-related tasks efficiently.

**Approach:** Create `docs/how-to/` directory with 5 focused guides following the how-to-guide template. Each guide covers one specific task: reviewing activities, exporting data, interpreting JSON, pausing/resuming tracking, and configuring settings. Since this is documentation-only, TDD uses file existence and content verification.

**Tech Stack:** Markdown documentation only (no code changes)

---

## Story Context

**Title:** Generate Core Task How-To Guides

**Description:** As a lawyer using SyncoPaid, I want step-by-step guides for common tasks so that I can efficiently accomplish my billing-related goals.

**Acceptance Criteria:**
- [ ] How to review tracked activities for a date range
- [ ] How to export activity data for billing
- [ ] How to interpret the exported JSON format
- [ ] How to pause/resume tracking
- [ ] How to configure tracking settings
- [ ] Each guide is single-task focused (one problem per guide)
- [ ] Each guide uses action verb headings and numbered steps

## Prerequisites

- [ ] docs/ directory exists (created by Story 21.3)
- [ ] getting-started.md exists as reference

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `docs/how-to/` | Create dir | How-to guides directory |
| `docs/how-to/review-tracked-activities.md` | Create | Guide for reviewing activities by date |
| `docs/how-to/export-activity-data.md` | Create | Guide for exporting to JSON |
| `docs/how-to/interpret-exported-json.md` | Create | Guide for understanding JSON format |
| `docs/how-to/pause-resume-tracking.md` | Create | Guide for pause/resume functionality |
| `docs/how-to/configure-tracking-settings.md` | Create | Guide for adjusting settings |

## Reference Material

**System Tray Menu:**
- ⏸ Pause Tracking / ▶ Start Tracking (toggle)
- 📊 Open SyncoPaid
- 🚀 Start with Windows (checkbox)
- ℹ About

**Export Functionality (exporter.py):**
- `export_to_json()`: Exports events with date range filtering
- Output includes: export_date, date_range, total_events, durations, events array
- Each event contains: timestamp, duration_seconds, app, title, url, is_idle

**Configuration Settings (config_defaults.py):**
- poll_interval_seconds (1.0)
- idle_threshold_seconds (180 = 3 minutes)
- screenshot_enabled (true)
- screenshot_interval_seconds (10)
- transition_prompt_enabled (true)

**Data Location:** `%LOCALAPPDATA%\SyncoPaid\`

---

## TDD Tasks

### Task 1: Create how-to directory and index (~3 min)

**Files:**
- Create: `docs/how-to/` directory
- Create: `docs/how-to/README.md`

**Context:** This task creates the directory structure for how-to guides. The README.md serves as an index linking to all guides in this section.

**Step 1 - RED:** Verify directory doesn't exist
```bash
test -d docs/how-to && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - Create directory:**
```bash
mkdir -p docs/how-to
```

**Step 3 - GREEN:** Create README.md with index
```markdown
# How-To Guides

Quick guides for common SyncoPaid tasks. Each guide focuses on a single task.

## Core Tasks

| Guide | Description | Time |
|-------|-------------|------|
| [Review Tracked Activities](./review-tracked-activities.md) | View and filter your activity history | 2 min |
| [Export Activity Data](./export-activity-data.md) | Export data for billing or analysis | 3 min |
| [Interpret Exported JSON](./interpret-exported-json.md) | Understand the export file format | 5 min |
| [Pause/Resume Tracking](./pause-resume-tracking.md) | Temporarily stop and restart tracking | 1 min |
| [Configure Tracking Settings](./configure-tracking-settings.md) | Adjust idle detection and screenshot settings | 3 min |

## Need Help?

- [Getting Started](../getting-started.md) - First-time setup
- [Troubleshooting](../troubleshooting.md) - Common issues
```

**Step 4 - Verify GREEN:**
```bash
test -f docs/how-to/README.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 5 - COMMIT:**
```bash
git add docs/how-to/ && git commit -m "docs: create how-to guides directory with index"
```

---

### Task 2: Create "Review Tracked Activities" guide (~5 min)

**Files:**
- Create: `docs/how-to/review-tracked-activities.md`

**Context:** Lawyers need to review their tracked activities to recall work done for billing. This guide shows how to open SyncoPaid and filter activities by date.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/how-to/review-tracked-activities.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create the guide
```markdown
# How to Review Tracked Activities

**Time required:** 2 minutes
**Prerequisites:** SyncoPaid running (green stopwatch in system tray)

## Overview

Review your tracked activities to see which applications and windows you worked with during a specific time period. This is useful for:
- Recalling what you worked on for billing
- Verifying time spent on a matter
- Identifying gaps in your workday

## Steps

### 1. Open the Activity Viewer

Right-click the SyncoPaid stopwatch icon in your system tray and select **📊 Open SyncoPaid**.

**Expected result:** The SyncoPaid window opens showing your recent activities.

### 2. Set Your Date Range

Use the date filters at the top of the window:
- Click the **Start Date** field and select the beginning of your range
- Click the **End Date** field and select the end of your range
- Click **Apply** to filter the list

**Tip:** For today's activities only, select today's date for both start and end.

### 3. Review the Activity List

The list shows:
- **Time** - When the activity started
- **Duration** - How long you spent in that window
- **Application** - The program name (e.g., "chrome.exe", "OUTLOOK.EXE")
- **Window Title** - The specific document, email, or page

**Tip:** Long window titles are truncated. Hover over a row to see the full title.

### 4. Filter by Application (Optional)

To see activities for just one program:
- Click the **Application** dropdown
- Select the application name
- The list updates to show only activities from that program

## Verification

You've successfully reviewed your activities when:
- You can see a list of applications and windows you used
- The date range matches the period you selected
- Activity durations are displayed in a readable format

## Troubleshooting

**Problem:** Activity list is empty
**Solution:** Check your date range. Ensure SyncoPaid was running during the period you selected.

**Problem:** Can't find a specific activity
**Solution:** Try expanding your date range or clearing the application filter.

## Related Guides

- [Export Activity Data](./export-activity-data.md) - Save activities to a file
- [Pause/Resume Tracking](./pause-resume-tracking.md) - Stop tracking during breaks
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/how-to/review-tracked-activities.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/how-to/review-tracked-activities.md && git commit -m "docs: add review-tracked-activities how-to guide"
```

---

### Task 3: Create "Export Activity Data" guide (~5 min)

**Files:**
- Create: `docs/how-to/export-activity-data.md`

**Context:** Lawyers need to export activity data to JSON for billing systems or LLM categorization. This guide covers the export process with date filtering.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/how-to/export-activity-data.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create the guide
```markdown
# How to Export Activity Data

**Time required:** 3 minutes
**Prerequisites:** SyncoPaid running with tracked activities

## Overview

Export your tracked activities to a JSON file for:
- Importing into billing software
- Sending to an LLM for automatic categorization
- Archiving for your records
- Sharing with your firm's billing department

## Steps

### 1. Open the Activity Viewer

Right-click the SyncoPaid stopwatch icon in your system tray and select **📊 Open SyncoPaid**.

**Expected result:** The SyncoPaid window opens.

### 2. Select Your Date Range

Before exporting, set the date range to include only the activities you need:
- Set **Start Date** and **End Date** for your billing period
- Click **Apply** to filter

**Tip:** Most lawyers export weekly or monthly. Choose dates that match your billing cycle.

### 3. Start the Export

Click the **Export** button in the toolbar.

**Expected result:** An export dialog opens.

### 4. Choose Export Options

In the export dialog:
- **File location:** Click Browse to choose where to save the file
- **Filename:** Use a descriptive name like `activities-2024-01-week1.json`
- **Include idle time:** Check this if you want to see breaks and idle periods

Click **Export** to create the file.

### 5. Locate Your Export File

After export completes:
- A confirmation message shows the file location
- The file is saved as JSON (readable by billing tools and LLMs)

**Default export location:** `%USERPROFILE%\Documents\SyncoPaid Exports\`

## Verification

To confirm your export worked:
- Navigate to the export location in File Explorer
- Verify the JSON file exists with the expected filename
- File size should be proportional to activities (typically 1KB-10KB per day)

## Troubleshooting

**Problem:** Export button is grayed out
**Solution:** Ensure you have activities in the selected date range.

**Problem:** File not found after export
**Solution:** Check the confirmation message for the exact file path. The default location is in your Documents folder.

**Problem:** Export file is very large
**Solution:** Narrow your date range or exclude idle time to reduce file size.

## Related Guides

- [Interpret Exported JSON](./interpret-exported-json.md) - Understand the export format
- [Review Tracked Activities](./review-tracked-activities.md) - Preview before exporting
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/how-to/export-activity-data.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/how-to/export-activity-data.md && git commit -m "docs: add export-activity-data how-to guide"
```

---

### Task 4: Create "Interpret Exported JSON" guide (~5 min)

**Files:**
- Create: `docs/how-to/interpret-exported-json.md`

**Context:** Once data is exported, lawyers or their billing software need to understand the JSON structure. This guide explains each field in the export.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/how-to/interpret-exported-json.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create the guide
```markdown
# How to Interpret Exported JSON

**Time required:** 5 minutes
**Prerequisites:** An exported JSON file from SyncoPaid

## Overview

SyncoPaid exports activity data as JSON (JavaScript Object Notation), a standard format readable by:
- Billing software systems
- AI tools like Claude or ChatGPT for categorization
- Spreadsheet programs (with conversion)
- Custom scripts

This guide explains each field so you can work with or verify your exported data.

## Export File Structure

Open your JSON file in any text editor (Notepad works fine). You'll see a structure like this:

```json
{
  "export_date": "2024-01-15T14:30:00.123456",
  "date_range": {
    "start": "2024-01-08",
    "end": "2024-01-14"
  },
  "total_events": 245,
  "total_duration_seconds": 28800.5,
  "active_duration_seconds": 25200.0,
  "idle_duration_seconds": 3600.5,
  "include_idle": true,
  "events": [ ... ]
}
```

## Field Definitions

### Header Fields

| Field | Meaning | Example |
|-------|---------|---------|
| `export_date` | When you created this export | "2024-01-15T14:30:00" |
| `date_range.start` | First day included | "2024-01-08" |
| `date_range.end` | Last day included | "2024-01-14" |
| `total_events` | Number of activity entries | 245 |
| `total_duration_seconds` | Total tracked time (active + idle) | 28800.5 (8 hours) |
| `active_duration_seconds` | Time actively working | 25200.0 (7 hours) |
| `idle_duration_seconds` | Time away from computer | 3600.5 (1 hour) |
| `include_idle` | Whether idle periods are included | true or false |

**Tip:** To convert seconds to hours, divide by 3600.

### Event Fields

Each entry in the `events` array represents one activity period:

```json
{
  "timestamp": "2024-01-15T09:15:30",
  "duration_seconds": 1245.5,
  "app": "OUTLOOK.EXE",
  "title": "RE: Johnson Matter - Settlement Discussion - Message",
  "url": null,
  "is_idle": false
}
```

| Field | Meaning | Example |
|-------|---------|---------|
| `timestamp` | When this activity started | "2024-01-15T09:15:30" |
| `duration_seconds` | How long you spent here | 1245.5 (about 21 minutes) |
| `app` | Application name | "OUTLOOK.EXE", "chrome.exe" |
| `title` | Window or document title | Email subject, document name |
| `url` | Web address (if browser) | "https://westlaw.com/..." or null |
| `is_idle` | Whether you were away | true or false |

## Converting Duration to Billing Time

Most law firms bill in 6-minute increments (0.1 hours). To convert:

1. Take `duration_seconds` (e.g., 1245.5)
2. Divide by 60 to get minutes (1245.5 ÷ 60 = 20.76 minutes)
3. Divide by 6 to get 0.1-hour units (20.76 ÷ 6 = 3.46 units)
4. Round to nearest 0.1 hour (3.5 units = 0.35 hours)

**Example:** 1245.5 seconds = 0.35 billable hours

## Verification

You've successfully interpreted the export when you can:
- Identify the date range covered
- Calculate total billable hours (active_duration_seconds ÷ 3600)
- Find specific activities by application or title
- Identify matter-related activities from window titles

## Troubleshooting

**Problem:** JSON appears as one long line
**Solution:** Use a JSON formatter (search "JSON formatter online") or open in VS Code with JSON extension.

**Problem:** Can't find specific activity
**Solution:** Use your text editor's Find function (Ctrl+F) to search for keywords.

**Problem:** Duration values seem wrong
**Solution:** Remember durations are in seconds. Divide by 60 for minutes, by 3600 for hours.

## Related Guides

- [Export Activity Data](./export-activity-data.md) - Create an export file
- [Review Tracked Activities](./review-tracked-activities.md) - View activities before exporting
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/how-to/interpret-exported-json.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/how-to/interpret-exported-json.md && git commit -m "docs: add interpret-exported-json how-to guide"
```

---

### Task 5: Create "Pause/Resume Tracking" guide (~3 min)

**Files:**
- Create: `docs/how-to/pause-resume-tracking.md`

**Context:** Lawyers may want to pause tracking during personal breaks, confidential meetings, or non-billable time. This is a simple task but important for accurate billing.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/how-to/pause-resume-tracking.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create the guide
```markdown
# How to Pause and Resume Tracking

**Time required:** 1 minute
**Prerequisites:** SyncoPaid running (icon visible in system tray)

## Overview

Pause tracking when you need to:
- Take a personal break
- Attend a confidential meeting that shouldn't be logged
- Step away for non-billable activities
- Handle personal matters during work hours

## Steps

### 1. Locate the SyncoPaid Icon

Find the stopwatch icon in your system tray (bottom-right corner, near the clock).

**Icon states:**
- **Green stopwatch** = Actively tracking
- **Orange stopwatch** = Paused by you
- **Faded stopwatch** = Automatically paused (inactive for 5 minutes)

### 2. Pause Tracking

Right-click the SyncoPaid icon and select **⏸ Pause Tracking**.

**Expected result:**
- Icon changes from green to orange
- Tooltip shows "SyncoPaid - Paused"
- No new activities are recorded

### 3. Resume Tracking

When ready to continue:

Right-click the SyncoPaid icon and select **▶ Start Tracking**.

**Expected result:**
- Icon changes back to green
- Tracking resumes immediately
- New activities are recorded from this moment forward

## Verification

To confirm tracking is paused:
- The system tray icon should be orange
- Hover over the icon to see "Paused" in the tooltip
- Switch between applications - no new activities should appear in the log

To confirm tracking has resumed:
- The system tray icon should be green
- Open the Activity Viewer to see new entries appearing

## Troubleshooting

**Problem:** Icon stays orange after clicking "Start Tracking"
**Solution:** Right-click and try again. If the issue persists, quit and restart SyncoPaid.

**Problem:** Activities still appearing while paused
**Solution:** Verify you clicked "Pause Tracking" - the menu item should now show "Start Tracking" when you right-click again.

**Problem:** Forgot to pause before a confidential meeting
**Solution:** You can delete specific activities from the Activity Viewer if needed.

## Related Guides

- [Review Tracked Activities](./review-tracked-activities.md) - Check what was recorded
- [Configure Tracking Settings](./configure-tracking-settings.md) - Adjust idle detection behavior
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/how-to/pause-resume-tracking.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/how-to/pause-resume-tracking.md && git commit -m "docs: add pause-resume-tracking how-to guide"
```

---

### Task 6: Create "Configure Tracking Settings" guide (~5 min)

**Files:**
- Create: `docs/how-to/configure-tracking-settings.md`

**Context:** Power users may want to adjust idle detection thresholds, screenshot settings, or startup behavior. This guide covers the most commonly adjusted settings.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/how-to/configure-tracking-settings.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create the guide
```markdown
# How to Configure Tracking Settings

**Time required:** 3 minutes
**Prerequisites:** SyncoPaid running

## Overview

Customize SyncoPaid to match your work style:
- Adjust how quickly idle time is detected
- Enable or disable screenshot capture
- Configure automatic startup
- Fine-tune transition prompts

## Steps

### 1. Open Settings

Right-click the SyncoPaid icon in your system tray, then select **📊 Open SyncoPaid**.

In the main window, click **Settings** (gear icon) or navigate to **File → Settings**.

**Expected result:** The Settings dialog opens.

### 2. Adjust Idle Detection

The idle threshold determines when SyncoPaid marks you as "away":

- Find **Idle Threshold** (measured in seconds)
- Default is **180 seconds** (3 minutes)
- Adjust based on your work style:
  - **60 seconds** - More aggressive, marks idle quickly
  - **180 seconds** - Balanced default
  - **300 seconds** - Relaxed, allows for reading/thinking

**Tip:** If you often read long documents without touching keyboard/mouse, increase this value.

### 3. Configure Screenshot Capture

Screenshots help provide context for your activities:

- **Screenshot Enabled** - Toggle on/off
- **Screenshot Interval** - How often to capture (default: 10 seconds)
- **Screenshot Quality** - JPEG quality (1-100, default: 65)

**Warning:** Disabling screenshots removes visual context that can be helpful for matter categorization.

### 4. Set Startup Behavior

Choose whether SyncoPaid starts automatically:

- **Start with Windows** - Also accessible from system tray menu
- **Start Tracking on Launch** - Begin tracking immediately when app opens

**Tip:** For lawyers, keeping both enabled ensures no billable time is missed.

### 5. Fine-tune Transition Prompts (Optional)

Transition prompts ask you to categorize work when you switch between matters:

- **Transition Prompts Enabled** - Toggle on/off
- **Sensitivity** - How aggressively to prompt
  - **Aggressive** - Prompt on every app switch
  - **Moderate** - Prompt on significant switches (default)
  - **Minimal** - Prompt only on major transitions

### 6. Save Settings

Click **Save** or **Apply** to save your changes.

**Expected result:** Settings are saved and take effect immediately.

## Common Settings

| Setting | Default | Recommended For |
|---------|---------|-----------------|
| Idle Threshold | 180s | Most users |
| Idle Threshold | 300s | Document reviewers |
| Screenshot Enabled | Yes | All users (provides context) |
| Screenshot Interval | 10s | Most users |
| Start with Windows | No | Lawyers (set to Yes) |
| Start Tracking on Launch | Yes | All users |

## Verification

To confirm your settings are applied:
1. Close and reopen SyncoPaid
2. Verify settings match what you configured
3. Test idle detection by stepping away for your configured threshold

## Troubleshooting

**Problem:** Settings reset after restart
**Solution:** Ensure you clicked Save before closing. Check that the config file is not read-only.

**Problem:** Idle detection seems off
**Solution:** Your idle threshold may need adjustment. Experiment with different values.

**Problem:** Too many transition prompts
**Solution:** Change sensitivity to "Minimal" or disable transition prompts entirely.

## Advanced: Manual Configuration

Settings are stored in:
```
%LOCALAPPDATA%\SyncoPaid\config.json
```

You can edit this file directly if needed, but use the Settings dialog for safety.

## Related Guides

- [Pause/Resume Tracking](./pause-resume-tracking.md) - Temporarily stop tracking
- [Review Tracked Activities](./review-tracked-activities.md) - See what's being captured
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/how-to/configure-tracking-settings.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/how-to/configure-tracking-settings.md && git commit -m "docs: add configure-tracking-settings how-to guide"
```

---

## Final Verification

Run after all tasks complete:
```bash
# Verify all files exist
echo "Checking how-to guides..."
test -d docs/how-to && echo "docs/how-to directory: OK"
test -f docs/how-to/README.md && echo "README.md: OK"
test -f docs/how-to/review-tracked-activities.md && echo "review-tracked-activities.md: OK"
test -f docs/how-to/export-activity-data.md && echo "export-activity-data.md: OK"
test -f docs/how-to/interpret-exported-json.md && echo "interpret-exported-json.md: OK"
test -f docs/how-to/pause-resume-tracking.md && echo "pause-resume-tracking.md: OK"
test -f docs/how-to/configure-tracking-settings.md && echo "configure-tracking-settings.md: OK"

# Count total files
echo ""
echo "Total guides created: $(ls docs/how-to/*.md | wc -l)"
```

Expected: All "OK" messages, 6 total files (5 guides + README)

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- Guides reference UI features (Activity Viewer, Settings dialog) that may not yet be fully implemented
- Screenshots/diagrams can be added in Story 21.6 (Visual Aids Strategy)
- Each guide follows the how-to-guide.md template pattern with action verb headings
- Troubleshooting sections included per template requirements
- Related Guides sections create cross-links between documentation
