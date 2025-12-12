---
name: story-tree
description: Use when user says "generate stories", "brainstorm features", "update story tree", "what should we build", or asks for feature ideas - autonomously maintains hierarchical story backlog by analyzing git commits, identifying under-capacity nodes, and generating evidence-based stories to fill gaps. Works with SQLite database using closure table pattern, prioritizes shallower nodes first, and tracks implementation status through commit analysis.
---

# Story Tree - Autonomous Hierarchical Backlog Manager

## Purpose

Maintain a **self-managing tree of user stories** where:
- Each node represents a story at some level of granularity
- Each node has a **capacity** (target number of child nodes)
- The skill autonomously identifies **under-capacity nodes** and generates stories to fill them
- Git commits are analyzed to mark stories as **implemented**
- Higher-level nodes are prioritized when under capacity

## Storage: SQLite with Closure Table

Story tree data is stored in `.claude/data/story-tree.db` using SQLite with a closure table pattern for efficient hierarchical queries.

**Why separate from skill folder:** The skill definition files (SKILL.md, schema.sql, lib/, docs/) are meant to be copied between projects. The database contains project-specific data and should not be copied to other projects, but it **should be tracked in version control** for the current project to maintain history of your backlog evolution.

**Important:** Ensure your `.gitignore` includes an exception for the story-tree database:
```
*.db
!.claude/data/story-tree.db
```

**Why SQLite over JSON:**
- Scales to 500+ stories without performance issues
- Single SQL query replaces recursive tree traversal
- Atomic transactions prevent data corruption
- Efficient queries for priority calculation

**Database location:** `.claude/data/story-tree.db`
**Schema reference:** `.claude/skills/story-tree/schema.sql`

### Core Tables

```sql
-- Story nodes table: all story data
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN ('concept','approved','rejected','planned','queued','active','in-progress','bugged','implemented','ready','deprecated','infeasible')),
    project_path TEXT,
    last_implemented TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Closure table: ancestor-descendant relationships at all depths
CREATE TABLE story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id),
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id),
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);

-- Commit tracking
CREATE TABLE story_node_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id),
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);

-- Metadata (version, lastUpdated, lastAnalyzedCommit)
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Status Values
- `concept`: Idea, not yet approved
- `approved`: Human reviewed and approved, not yet planned
- `rejected`: Human reviewed and rejected
- `planned`: Implementation plan has been created
- `queued`: Plan ready, all dependencies implemented
- `active`: Currently being worked on
- `in-progress`: Partially complete
- `bugged`: In need of debugging
- `implemented`: Complete/done
- `ready`: Production ready, implemented and tested
- `deprecated`: No longer relevant
- `infeasible`: Couldn't build it

## Tree Structure Concepts

### Node Levels
- **Level 0 (Root)**: Product vision ("SaaS Apps for Lawyers")
- **Level 1**: App ideas ("Evidence management app")
- **Level 2**: Major features ("Upload evidence", "Deduplicate files")
- **Level 3**: Specific capabilities ("Drag-and-drop UI", "Hash-based dedup")
- **Level 4+**: Implementation details (as granular as needed)

### Closure Table Concept

The `story_paths` table stores ALL ancestor-descendant pairs, not just parent-child:

```
For tree: root → 1.1 → 1.1.1

story_paths contains:
| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root        | root          | 0     |  -- self
| root        | 1.1           | 1     |  -- root's child
| root        | 1.1.1         | 2     |  -- root's grandchild
| 1.1         | 1.1           | 0     |  -- self
| 1.1         | 1.1.1         | 1     |  -- 1.1's child
| 1.1.1       | 1.1.1         | 0     |  -- self
```

This enables efficient subtree queries without recursion.

## When NOT to Use

**Do NOT use this skill for:**

1. **Creating 1-3 specific stories manually** - Just create them directly in your backlog tool
2. **Non-hierarchical backlogs** - This skill assumes tree structure
3. **Projects without git history** - Pattern detection requires commits
4. **Real-time task tracking** - This is for planning, not daily task management
5. **Detailed implementation planning** - Use `superpowers:writing-plans` instead
6. **Non-software projects** - Assumes codebase with git commits

## Autonomous Operation Mode

**This skill operates autonomously by default.** When the user says "update story tree" or "generate stories," you should:

1. **Run the complete workflow** (Steps 1-7) without asking permission for each step
2. **Generate stories** based on git analysis and priority algorithm
3. **Output the complete report** when finished
4. **Ask for clarification ONLY when**:
   - Over-capacity violations are detected (see `lib/capacity-management.md`)
   - Multiple equally-valid priority targets exist
   - Git history is ambiguous or missing

## Auto-Update on Staleness

**On ANY skill invocation**, before processing the user's command:

1. **Check metadata table** for `lastUpdated` timestamp
2. **Compare to today's date**
3. **If more than 3 days old** → Automatically run the full "Update story tree" workflow first
4. **Then** proceed with the user's original command

```sql
-- Check staleness
SELECT value FROM metadata WHERE key = 'lastUpdated';
-- Compare: if (today - lastUpdated) >= 3 days, run update
```

## Autonomous Operation Workflow

### Step 1: Load Current Tree

Connect to `.claude/data/story-tree.db`. If database doesn't exist, create the data directory, initialize with schema, and seed root node.

```bash
# Create data directory if needed
mkdir -p .claude/data

# Check if database exists
test -f .claude/data/story-tree.db

# Initialize if needed
sqlite3 .claude/data/story-tree.db < .claude/skills/story-tree/schema.sql
```

### Step 2: Analyze Git Commits

**Use incremental analysis** to minimize context usage:

```bash
# Get last analyzed commit from metadata
sqlite3 .claude/data/story-tree.db "SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit';"

# If checkpoint valid: Incremental (only new commits)
git log <lastAnalyzedCommit>..HEAD --pretty=format:"%h|%ai|%s|%b" --no-merges

# If checkpoint missing/invalid: Full 30-day scan
git log --since="30 days ago" --pretty=format:"%h|%ai|%s|%b" --no-merges
```

**Checkpoint validation:** Before using the checkpoint, verify it still exists in git history:
```bash
git cat-file -t <lastAnalyzedCommit>
```

If validation fails (commit rebased away or missing), **log the reason** before falling back:
- Missing checkpoint: "No checkpoint found. Running full 30-day scan."
- Invalid checkpoint: "Checkpoint `abc123` no longer exists (likely rebased). Running full 30-day scan."

This logging helps users understand why analysis is slower than expected.

**After analysis, update checkpoint:**
```sql
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', '<newest_commit_hash>');
```

### Step 3: Calculate Tree Metrics

Use SQL to calculate metrics efficiently:

```sql
-- Get all stories with their depth and child count
SELECT
    s.*,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
FROM story_nodes s;
```

### Step 4: Identify Priority Target

**Priority algorithm** - find under-capacity nodes, prioritize shallower:

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
FROM story_nodes s
WHERE s.status != 'deprecated'
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) < s.capacity
ORDER BY node_depth ASC,
    (child_count * 1.0 / s.capacity) ASC
LIMIT 1;
```

**Rules:**
- Root under capacity? → Generate level-1 app ideas
- Level-1 under capacity? → Generate level-2 major features
- All higher levels at capacity? → Drill to deepest under-capacity node

### Step 5: Generate Stories for Target Node

Based on target node's level and context:

**If Level 1 (app ideas)**:
- Analyze root vision
- Review existing sibling apps
- Generate: 1-3 new app concepts with capacity 5-10 each

**If Level 2 (major features)**:
- Read parent app description
- Analyze git commits for what exists
- Generate: 1-5 major feature ideas with capacity 3-8 each

**If Level 3+ (specific capabilities)**:
- Read parent feature description
- Check git commits for implementation status
- Generate: 2-4 specific capability ideas with capacity 2-4 each

**Story format:**

```markdown
### [ID]: [Title]

**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Suggested capacity**: [N]
**Rationale**: [Why this makes sense]
**Related context**: [Git commits or patterns]
```

### Step 6: Update Tree

Insert generated stories into SQLite:

```sql
-- Insert story
INSERT INTO story_nodes (id, title, description, capacity, status, created_at, updated_at)
VALUES (:new_id, :title, :description, :capacity, 'concept', datetime('now'), datetime('now'));

-- Populate closure table (critical: includes self + all ancestors)
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, :new_id, depth + 1
FROM story_paths WHERE descendant_id = :parent_id
UNION ALL SELECT :new_id, :new_id, 0;
```

Update metadata:
```sql
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));
```

### Step 7: Output Report

Generate a comprehensive report (see "Report Format" section below).

## Capacity Estimation Logic

When generating stories, estimate capacity based on complexity:

- **Simple action** (single UI component): capacity = 2-3
- **Feature with workflow** (multiple steps): capacity = 5-8
- **Major feature** (end-to-end system): capacity = 8-12
- **Cross-cutting concern** (affects multiple areas): capacity = 10-15

## Implementation Detection

Match git commits to stories using fuzzy keyword matching:

```sql
-- Link commit to story
INSERT INTO story_node_commits (story_id, commit_hash, commit_date, commit_message)
VALUES (:story_id, :commit_hash, :commit_date, :commit_message);

-- Update story status based on commit matches
UPDATE story_nodes SET status = 'implemented', last_implemented = :commit_date
WHERE id = :story_id AND status IN ('planned', 'in-progress');
```

## Report Format

```markdown
# Story Tree Update Report
Generated: [ISO timestamp]

## Current Tree Status

### Overall Metrics
- Total nodes: [N]
- Implemented: [N] ([%]%)
- In progress: [N] ([%]%)
- Planned: [N] ([%]%)
- Concept: [N] ([%]%)

### Capacity Analysis
[SQL results showing capacity vs children per level]

## Git Commit Analysis
- Total commits analyzed: [N]
- Stories matched to commits: [list]
- Implementation progress updates: [list]

## Priority Target Identified

**Node**: [ID] "[Story title]"
- **Level**: [N]
- **Current children**: [N]
- **Capacity**: [N]
- **Why prioritized**: [Explanation]

## Generated Stories

[Full story format for each generated story]

## Tree Visualization

\`\`\`bash
# Run tree-view.py for current structure
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii
\`\`\`

## Next Priority Target

After this update, next under-capacity node:
**Node**: [ID] "[Story title]"
```

## User Commands

The skill responds to these natural language commands:

- **"Update story tree"**: Run incremental analysis, identify priorities, generate stories
- **"Show story tree"**: Output current tree visualization
- **"Tree status"**: Show metrics and priorities without generating stories
- **"Set capacity for [node-id] to [N]"**: Adjust node capacity
- **"Mark [node-id] as [status]"**: Change node status
- **"Generate stories for [node-id]"**: Force story generation for specific node
- **"Initialize story tree"**: Create new database from scratch
- **"Export story tree to JSON"**: Export tree to nested JSON format
- **"Export story tree to markdown"**: Export tree as markdown document
- **"Show recent commits"**: Display git analysis without updating tree
- **"Rebuild story tree index"**: Force full 30-day rescan

## Tree Visualization Script

For any tree visualization needs, use the `tree-view.py` script rather than constructing ASCII trees manually:

```bash
# Full tree with capacity and status indicators
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii

# Subtree from a specific node with depth limit
python .claude/skills/story-tree/tree-view.py --root 1.1 --depth 2

# Filter by status (e.g., only implemented stories)
python .claude/skills/story-tree/tree-view.py --status implemented --compact

# Markdown format for documentation
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity

# Exclude deprecated stories
python .claude/skills/story-tree/tree-view.py --status deprecated --exclude-status
```

**When to use:**
- Generating report tree visualization (Step 7)
- Answering user questions about tree structure
- Creating documentation that shows tree state
- Debugging tree integrity issues

**Status symbols (ASCII):** `.` concept, `v` approved, `x` rejected, `o` planned, `@` queued, `*` active, `~` in-progress, `!` bugged, `+` implemented, `#` ready, `-` deprecated, `0` infeasible

**Note:** Use `--force-ascii` on Windows cmd.exe to avoid encoding issues.

### Export Commands

For human inspection and backup:

```bash
# Export to JSON (reconstructs nested structure from SQL)
sqlite3 .claude/data/story-tree.db "SELECT * FROM story_nodes;" | python -c "
import sys, json
# Reconstruct nested JSON from flat SQL output
..."

# Export to markdown
sqlite3 .claude/data/story-tree.db -markdown "
SELECT s.id, s.title, s.status,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children,
    s.capacity
FROM story_nodes s
ORDER BY s.id;
"
```

## Initial Tree Setup

When database doesn't exist, initialize with schema and seed root **based on the current project**:

### Step 1: Detect Project Metadata

Read project information from `package.json`:

```bash
# Extract project name and description
python -c "
import json
with open('package.json', 'r') as f:
    pkg = json.load(f)
    print(f'NAME:{pkg.get(\"name\", \"Unknown Project\")}')
    print(f'DESC:{pkg.get(\"description\", \"\")}')
"
```

If `package.json` doesn't exist or lacks description, read from `CLAUDE.md`:

```bash
# Extract project description from CLAUDE.md
grep -A 2 "^## .*Project Overview" CLAUDE.md | grep -v "^##" | grep -v "^--"
```

**Fallback defaults if no metadata found:**
- Title: `"Software Project"`
- Description: `"Software project story tree"`

### Step 2: Initialize Database

**CRITICAL:** The root node should represent **this specific project**, not a multi-app portfolio.

```bash
# Create data directory
mkdir -p .claude/data

# Initialize schema
cat .claude/skills/story-tree/schema.sql | python -c "
import sqlite3
import sys
import json

# Read schema from stdin
schema = sys.stdin.read()

# Connect to database
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Apply schema
cursor.executescript(schema)

# Read project metadata from package.json
try:
    with open('package.json', 'r') as f:
        pkg = json.load(f)
        project_name = pkg.get('name', 'Software Project')
        project_desc = pkg.get('description', '')

        # If no description in package.json, try to extract from CLAUDE.md
        if not project_desc:
            try:
                with open('CLAUDE.md', 'r') as cf:
                    for line in cf:
                        if 'Project:' in line or 'project' in line.lower():
                            project_desc = line.strip()
                            break
            except:
                pass

        # Final fallback
        if not project_desc:
            project_desc = f'{project_name} - Software project story tree'

except FileNotFoundError:
    project_name = 'Software Project'
    project_desc = 'Software project story tree'

# Insert root node (represents THIS project)
cursor.execute('''
    INSERT INTO story_nodes (id, title, description, capacity, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
''', ('root', project_name, project_desc, 10, 'active'))

# Root self-reference in closure table
cursor.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    VALUES ('root', 'root', 0)
''')

# Metadata
cursor.execute(\"INSERT INTO metadata (key, value) VALUES ('version', '2.0.0')\")
cursor.execute(\"INSERT INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))\")

conn.commit()
conn.close()

print(f'Initialized story tree for: {project_name}')
"
```

### Alternative: SQL-Only Initialization

If you prefer pure SQL without Python metadata detection:

```sql
-- Apply schema
.read schema.sql

-- Insert root node (CUSTOMIZE THIS FOR YOUR PROJECT)
INSERT INTO story_nodes (id, title, description, capacity, status, created_at, updated_at)
VALUES (
    'root',
    'YourProjectName',  -- ⚠️ CHANGE THIS to your actual project name
    'Your project description',  -- ⚠️ CHANGE THIS to describe your project
    10,
    'active',
    datetime('now'),
    datetime('now')
);

-- Root self-reference in closure table
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
VALUES ('root', 'root', 0);

-- Metadata
INSERT INTO metadata (key, value) VALUES ('version', '2.0.0');
INSERT INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));
```

### Why This Approach?

**ANTI-PATTERN (OLD):** Creating a portfolio-level root ("SaaS Apps for lawyers") with project as child.
- ❌ Assumes multi-app portfolio
- ❌ Hardcodes business domain
- ❌ Creates unnecessary nesting
- ❌ Database lives in ONE repo but tracks MANY apps

**CORRECT (NEW):** Project-specific root based on current repository.
- ✅ Each repo's `.claude/data/story-tree.db` tracks ONLY that project
- ✅ Root represents the actual software being built
- ✅ Auto-detects project name from package.json
- ✅ No hardcoded assumptions about business domain

## Quality Checks

Before outputting generated stories, verify:
- [ ] Each story has clear basis in commit history or logical gap analysis
- [ ] Stories are specific and actionable
- [ ] Acceptance criteria are testable
- [ ] No duplicate suggestions
- [ ] Stories align with existing architecture patterns
- [ ] User story format is complete

## Files Reference

- **`.claude/data/story-tree.db`**: SQLite database (primary data store, project-specific)
- **schema.sql**: Reference schema with query examples
- **tree-view.py**: Python CLI for ASCII/markdown tree visualization
- **lib/tree-analyzer.md**: SQL-based tree analysis algorithms
- **lib/pattern-matcher.md**: Git commit → story matching logic
- **lib/capacity-management.md**: Handling capacity issues
- **docs/tree-structure.md**: Detailed schema documentation
- **docs/migration-guide.md**: JSON to SQLite migration instructions
- **docs/common-mistakes.md**: Common pitfalls and how to avoid them

## Version History

- v2.0.0 (2025-12-11): **Breaking change** - Migrated from JSON to SQLite with closure table pattern for scalability (200-500 stories). See docs/migration-guide.md for migration instructions.
- v1.3.0 (2025-12-11): Added incremental commit analysis with checkpoint tracking
- v1.2.0 (2025-12-11): Added auto-update on staleness (3-day threshold)
- v1.1.0 (2025-12-11): Added autonomous mode guidance, "When NOT to Use" section
- v1.0.0 (2025-12-11): Initial release
