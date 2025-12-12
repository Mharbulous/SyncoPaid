# Tree Visualization Tool - User Guide

**Script:** `tree-view.py`
**Purpose:** Generate human-readable ASCII/markdown visualizations of your story tree database

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Status Symbols](#status-symbols)
3. [Common Use Cases](#common-use-cases)
4. [Command-Line Options](#command-line-options)
5. [Example Workflows](#example-workflows)
6. [Pro Tips](#pro-tips)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Usage

```bash
# Navigate to project root first
cd /path/to/your/project

# View entire tree with capacity and status
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii

# View specific subtree
python .claude/skills/story-tree/tree-view.py --root 1.2 --show-capacity --force-ascii

# Filter by status
python .claude/skills/story-tree/tree-view.py --status concept --show-capacity --force-ascii
```

**Windows users:** Always include `--force-ascii` to avoid Unicode encoding errors in cmd.exe.

### Getting Help

```bash
python .claude/skills/story-tree/tree-view.py --help
```

---

## Status Symbols

The `--show-status` flag adds status indicators to each node.

### Symbol Reference

| Symbol | Status | Meaning |
|--------|--------|---------|
| `*` | active | Root node (actively being developed) |
| `+` | implemented | Feature is complete and in codebase |
| `~` | in-progress | Currently working on this feature |
| `o` | planned | Accepted for development, not started |
| `.` | concept | Idea stage, not yet planned |
| `x` | deprecated | No longer relevant, cancelled |

### Capacity Format

When using `--show-capacity`, you'll see `[children/capacity]` after each node title:

- `[9/10]` = 9 children out of 10 capacity (90% full)
- `[2/4]` = 2 children out of 4 capacity (50% full)
- `[0/5]` = 0 children out of 5 capacity (empty, needs stories)

**Example output:**
```
TimeLawg - Automatic time tracking [9/10] ~
+-- Core activity tracking [4/5] +
+-- Screenshot capture [4/6] +
\-- Settings and Preferences UI [0/5] .
```

---

## Common Use Cases

### 1. Overview of Entire Tree

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii --depth 2
```

**Shows:** Top 2 levels with capacity utilization and status indicators

**Use when:** You want a high-level view of all major features without overwhelming detail

**Example output:**
```
TimeLawg - Automatic time tracking [9/10] ~
+-- Core activity tracking [4/5] +
|   +-- Poll active window [0/0] +
|   +-- Detect idle time [0/0] +
|   +-- Track timestamps [0/0] +
|   \-- Focus change detection [0/0] +
+-- Screenshot capture [4/6] +
\-- Settings UI [0/5] .
```

---

### 2. Deep Dive into Specific Feature

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --root 1.8 --show-capacity --show-status --force-ascii
```

**Shows:** Everything under node 1.8 with full depth (no limit)

**Use when:** Planning detailed work on a specific feature area

**Example output:**
```
Time entry states [5/6] o
+-- State data model [3/3] +
|   +-- Add state column [0/0] +
|   +-- Client matter validation [0/0] +
|   \-- State conversion rules [0/0] +
+-- System state assignment [5/5] .
|   +-- Active state [0/0] .
|   +-- Inactive state [0/0] .
|   \-- Paused state [0/0] .
\-- User state assignment [4/4] .
```

---

### 3. Find What Needs Work (Concepts Only)

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --status concept --show-capacity --force-ascii
```

**Shows:** Only concept-stage stories (not started yet)

**Use when:** Looking for new features to implement or planning next sprint

**Example output:**
```
# Filtered results (15 nodes matching criteria):
# (Tree structure unavailable - ancestors excluded by filter)

7.1.1: State transition logging [0/2]
7.1.2: Deletion audit trail [0/2]
7.1.3: Gap analysis [0/2]
8.2.1: Active state assignment [0/0]
8.2.2: Inactive state assignment [0/0]
...
```

---

### 4. Review Completed Work

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --status implemented --compact --force-ascii
```

**Shows:** Only implemented features in compact format (ID + title only)

**Use when:** Generating release notes or progress reports

**Example output:**
```
# Filtered results (29 nodes matching criteria):

1: Core activity tracking
1.1: Poll active window at configurable interval
1.2: Detect idle time from keyboard/mouse inactivity
1.3: Track start time, duration, and end time
2: Screenshot capture
2.1: Periodic screenshot capture
...
```

---

### 5. Hide Deprecated Stories

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --status deprecated --exclude-status --show-status --force-ascii
```

**Shows:** Everything EXCEPT deprecated stories

**Use when:** You want a clean view without old/cancelled features cluttering the output

**Note:** `--exclude-status` inverts the filter (exclude instead of include)

---

### 6. Export to Markdown for Documentation

**Command:**
```bash
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity > docs/story-tree.md
```

**Creates:** Markdown file with nested bullet list structure

**Use when:** Creating documentation or sharing tree structure with team

**Example output:**
```markdown
- **TimeLawg - Automatic time tracking** [9/10]
  - **1 Core activity tracking** [4/5]
    - 1.1 Poll active window [0/0]
    - 1.2 Detect idle time [0/0]
  - **2 Screenshot capture** [4/6]
```

---

## Command-Line Options

### Filtering Options

| Option | Description | Example |
|--------|-------------|---------|
| `--root ID` | Start tree from specific node | `--root 1.8` |
| `--depth N` | Limit display to N levels deep | `--depth 3` |
| `--status STATUS` | Filter by status (can use multiple times) | `--status concept --status planned` |
| `--exclude-status` | Exclude specified statuses instead | `--status deprecated --exclude-status` |

### Display Options

| Option | Description | Example |
|--------|-------------|---------|
| `--show-capacity` | Show [children/capacity] format | `--show-capacity` |
| `--show-status` | Show status indicator symbols | `--show-status` |
| `--compact` | Minimal output: ID + title only | `--compact` |
| `--verbose` | Include description (truncated to 60 chars) | `--verbose` |
| `--no-color` | Disable ANSI color codes | `--no-color` |
| `--force-ascii` | Use ASCII-only (no Unicode) | `--force-ascii` |

### Format Options

| Option | Description | Example |
|--------|-------------|---------|
| `--format ascii` | Tree with box-drawing chars (default) | `--format ascii` |
| `--format simple` | Simple indentation, no box chars | `--format simple` |
| `--format markdown` | Markdown nested list | `--format markdown` |

### Database Options

| Option | Description | Example |
|--------|-------------|---------|
| `--db PATH` | Custom database path | `--db /custom/path/story-tree.db` |

**Default:** Script auto-detects database at `.claude/data/story-tree.db` relative to project root.

---

## Example Workflows

### Workflow 1: Planning Sprint Work

```bash
# Step 1: See what's not implemented yet
python .claude/skills/story-tree/tree-view.py --status concept --status planned --show-capacity --force-ascii

# Step 2: Pick a feature and drill down (e.g., node 9)
python .claude/skills/story-tree/tree-view.py --root 9 --show-status --force-ascii

# Step 3: After implementing, verify what's done
python .claude/skills/story-tree/tree-view.py --status implemented --depth 2 --force-ascii

# Step 4: Export full tree for sprint retrospective
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity --show-status > sprint-retrospective.md
```

---

### Workflow 2: Finding Under-Capacity Nodes

```bash
# Step 1: View full tree with capacity indicators
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii

# Step 2: Identify nodes with low children/capacity ratio
# Look for patterns like [1/5], [0/4], [2/8]

# Step 3: Drill into specific under-capacity node (e.g., node 7)
python .claude/skills/story-tree/tree-view.py --root 7 --show-capacity --show-status --force-ascii

# Step 4: Generate new stories for that node using story-tree skill
# (Use Claude: "generate stories for node 7")
```

---

### Workflow 3: Progress Reporting

```bash
# What's been completed this week
python .claude/skills/story-tree/tree-view.py --status implemented --compact --force-ascii > completed.txt

# What's currently in progress
python .claude/skills/story-tree/tree-view.py --status in-progress --show-status --force-ascii

# What's up next (planned)
python .claude/skills/story-tree/tree-view.py --status planned --show-capacity --force-ascii

# Full status report in markdown
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity --show-status > weekly-report.md
```

---

## Pro Tips

### 1. Always Use `--force-ascii` on Windows

Windows cmd.exe doesn't handle Unicode box-drawing characters well. Always include this flag:

```bash
# Good (Windows)
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii

# Bad (Windows) - may cause encoding errors
python .claude/skills/story-tree/tree-view.py --show-capacity
```

**Linux/Mac users:** You can omit `--force-ascii` for prettier Unicode output.

---

### 2. Combine Multiple Status Filters

You can specify `--status` multiple times to show multiple statuses:

```bash
# Show both concept AND planned stories
python .claude/skills/story-tree/tree-view.py --status concept --status planned --force-ascii
```

---

### 3. Save Output to Files

Use shell redirection to save results:

```bash
# Save to text file
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii > tree-snapshot.txt

# Save markdown to docs folder
python .claude/skills/story-tree/tree-view.py --format markdown > docs/backlog.md
```

---

### 4. Find Under-Capacity Nodes Quickly

Look for low ratios in the capacity indicators:

- `[0/5]` = 0% full → **needs stories urgently**
- `[1/4]` = 25% full → **under-capacity, needs more**
- `[3/4]` = 75% full → **almost full**
- `[4/4]` = 100% full → **at capacity**

---

### 5. Use `--root` to Focus Without Distraction

When working on a specific feature area, use `--root` to show only that subtree:

```bash
# Focus on just the "Time entry states" feature
python .claude/skills/story-tree/tree-view.py --root 8 --show-capacity --show-status --force-ascii
```

This is cleaner than viewing the entire tree and mentally filtering.

---

### 6. Exclude Deprecated Stories for Clean Views

Add `--status deprecated --exclude-status` to hide old/cancelled features:

```bash
python .claude/skills/story-tree/tree-view.py --status deprecated --exclude-status --show-status --force-ascii
```

---

## Troubleshooting

### Error: "Database error: no such table: story_nodes"

**Cause:** Database doesn't exist or is corrupted (0 bytes)

**Solution:**
```bash
# Check database size
ls -lh .claude/data/story-tree.db

# If 0 bytes, restore from backup or reinitialize
cp .claude/data/story-tree.db.backup-YYYYMMDD .claude/data/story-tree.db
```

---

### Error: "Could not find story-tree.db"

**Cause:** Script can't auto-detect database location

**Solution:** Specify path explicitly with `--db`:
```bash
python .claude/skills/story-tree/tree-view.py --db /full/path/to/story-tree.db --force-ascii
```

---

### Error: UnicodeEncodeError on Windows

**Cause:** Windows cmd.exe can't encode Unicode characters

**Solution:** Add `--force-ascii` flag:
```bash
python .claude/skills/story-tree/tree-view.py --show-status --force-ascii
```

---

### Error: "No nodes found for root 'X'"

**Cause:** Specified root node doesn't exist in database

**Solution:** Check valid node IDs first:
```bash
# List all nodes in compact format
python .claude/skills/story-tree/tree-view.py --compact --force-ascii
```

Then use a valid node ID with `--root`.

---

### Filtered Results Show "Tree structure unavailable"

**Cause:** Status filter excluded all ancestor nodes, so tree can't be built

**Example:**
```bash
python .claude/skills/story-tree/tree-view.py --status implemented --force-ascii
```

If only leaf nodes are implemented, their parent nodes (concept/planned) are excluded, breaking the tree structure.

**Result:** Script shows a flat list instead of tree:
```
# Filtered results (7 nodes matching criteria):
# (Tree structure unavailable - ancestors excluded by filter)

1.1: Poll active window
1.2: Detect idle time
...
```

**This is normal behavior** - use `--compact` for cleaner flat list output.

---

## Integration with Story-Tree Skill

The `tree-view.py` script is used by the story-tree skill for generating visualizations in autonomous reports. When Claude runs "update story tree", it automatically invokes this script.

You can also run it manually anytime to inspect your backlog state without triggering the full skill workflow.

---

## Advanced: Scripting with tree-view.py

### Count Stories by Status

```bash
# Count concept stories
python .claude/skills/story-tree/tree-view.py --status concept --compact --force-ascii | wc -l

# Count implemented features
python .claude/skills/story-tree/tree-view.py --status implemented --compact --force-ascii | wc -l
```

### Generate Daily Snapshot

```bash
#!/bin/bash
# Save daily snapshot with timestamp
DATE=$(date +%Y-%m-%d)
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii > snapshots/tree-$DATE.txt
```

### Monitor Progress Over Time

```bash
# Compare today's implemented count vs last week
python .claude/skills/story-tree/tree-view.py --status implemented --compact --force-ascii > today.txt
wc -l today.txt
wc -l snapshots/tree-2024-12-01.txt
```

---

## Summary

**Most Common Commands:**

```bash
# Quick overview
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii --depth 2

# Drill into feature
python .claude/skills/story-tree/tree-view.py --root NODE_ID --show-capacity --force-ascii

# Find what to work on next
python .claude/skills/story-tree/tree-view.py --status concept --status planned --force-ascii

# Export to markdown
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity > docs/backlog.md
```

**Remember:**
- Use `--force-ascii` on Windows
- `--show-capacity` reveals under-capacity nodes
- `--show-status` shows implementation progress
- `--root` focuses on specific features
- Redirect to files with `> output.txt`

---

**Questions or Issues?**

See `SKILL.md` for skill documentation or check `docs/common-mistakes.md` for troubleshooting database issues.
