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

**Design rationale:** If instructions seem counter-intuitive or you're tempted to deviate, consult `docs/rationale.md` before changing approach.

## Storage: SQLite with Closure Table

Story tree data is stored in `.claude/data/story-tree.db` using SQLite with a closure table pattern for efficient hierarchical queries.

**Important:** Ensure your `.gitignore` includes an exception for the story-tree database:
```
*.db
!.claude/data/story-tree.db
```

**Database location:** `.claude/data/story-tree.db`
**Schema reference:** `.claude/skills/story-tree/schema.sql`

### Core Tables

```sql
-- Story nodes table: all story data
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,  -- Optional override; if NULL, use dynamic: 3 + implemented children
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
CREATE TABLE story_commits (
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
- concept: Idea, not yet approved
- approved: Human reviewed and approved, not yet planned
- rejected: Human reviewed and rejected
- planned: Implementation plan has been created
- queued: Plan ready, all dependencies implemented
- active: Currently being worked on
- in-progress: Partially complete
- bugged: In need of debugging
- implemented: Complete/done
- ready: Production ready, implemented and tested
- deprecated: No longer relevant
- infeasible: Couldn't build it

## Tree Structure Concepts

### Node Levels
- **Level 0 (Root)**: App idea ("Evidence management app")
- **Level 1**: Major features ("Upload evidence", "Deduplicate files")
- **Level 2**: Specific capabilities ("Drag-and-drop UI", "Hash-based dedup")
- **Level 3+**: Implementation details (as granular as needed)

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

If validation fails (commit rebased away or missing), log the reason before falling back to full 30-day scan.

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

**Do not autonomously expand nodes with status:** `concept` (unapproved), `rejected`, `deprecated`, `infeasible`, or `bugged`.

**Priority algorithm** - find under-capacity nodes, prioritize shallower:

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    -- Use capacity override if set, otherwise dynamic: 3 + implemented/ready children
    COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
         JOIN story_nodes child ON sp.descendant_id = child.id
         WHERE sp.ancestor_id = s.id AND sp.depth = 1
         AND child.status IN ('implemented', 'ready'))) as effective_capacity
FROM story_nodes s
WHERE s.status NOT IN ('concept', 'rejected', 'deprecated', 'infeasible', 'bugged')
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
      COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
           JOIN story_nodes child ON sp.descendant_id = child.id
           WHERE sp.ancestor_id = s.id AND sp.depth = 1
           AND child.status IN ('implemented', 'ready')))
ORDER BY node_depth ASC
LIMIT 1;
```

**Rules:**
- Root under capacity? → Generate level-1 features
- Level-1 under capacity? → Generate level-2 capabilities
- All higher levels at capacity? → Drill to deepest under-capacity node

### Human Override

**When user explicitly requests** "add concept to [node-id]" or "generate stories for [node-id]":
1. Skip the status filter for that specific node
2. Add the requested concepts
3. Note in the report that this was a manual override

```sql
-- Manual override query (only block deprecated nodes)
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
FROM story_nodes s
WHERE s.id = :user_specified_node_id
  AND s.status NOT IN ('deprecated', 'rejected', 'infeasible');
```

### Step 5: Generate Stories for Target Node

Based on target node's level and context:

**HARD LIMIT: Maximum 3 concepts per node per invocation.**

**If Level 1 (major features)**:
- Analyze root vision
- Review existing sibling features
- Generate: 1-3 new feature concepts

**If Level 2 (specific capabilities)**:
- Read parent feature description
- Analyze git commits for what exists
- Generate: 1-3 capability ideas

**If Level 3+ (implementation details)**:
- Read parent capability description
- Check git commits for implementation status
- Generate: 1-3 specific implementation ideas

New nodes start with capacity 3. Capacity grows as children are implemented.

**Story format:**

```markdown
### [ID]: [Title]

**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context**: [Git commits or patterns]
```

### Step 6: Update Tree

Insert generated stories into SQLite:

```sql
-- Insert story (capacity is NULL, uses dynamic calculation)
INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
VALUES (:new_id, :title, :description, 'concept', datetime('now'), datetime('now'));

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

## Dynamic Capacity

Node capacity is computed dynamically:
```
effective_capacity = capacity_override OR (3 + count of implemented/ready children)
```

This ensures the tree grows organically based on actual progress. Set `capacity` in the database to override for specific nodes.

## Implementation Detection

Match git commits to stories using fuzzy keyword matching:

```sql
-- Link commit to story
INSERT INTO story_commits (story_id, commit_hash, commit_date, commit_message)
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
- **"Show story tree"**: Output current tree visualization (see "CRITICAL: Presenting Tree Diagrams to Users" section below - you MUST save output to file and present it properly)
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

For any tree visualization needs, use the `tree-view.py` script rather than constructing ASCII trees manually.

### CRITICAL: Presenting Tree Diagrams to Users

**Problem:** Claude Code truncates bash command output (e.g., showing `... +42 lines`). When you run `tree-view.py`, the user often cannot see the actual tree diagram.

**Solution:** When the user asks to "show the story tree" or "show a diagram", you MUST:

1. **Capture output to a file**, then read and present it:
   ```bash
   # Save output to temp file
   python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii > /tmp/story-tree-output.txt
   ```

2. **Read the file using the Read tool** (not cat/bash)

3. **Present the tree in your response text** as a properly formatted code block:
   ```
   Here's your current story tree:

   \`\`\`
   ListBot [8/10] O
   +-- (1) File Upload & Deduplication [8/8] +
   |   +-- (1.1) Hash-Based File Deduplication [0/4] +
   |   +-- (1.2) Drag-and-Drop Upload Interface [0/3] +
   ...
   \`\`\`
   ```

4. **Add a legend and insights** after the tree:
   - Explain the status symbols (`.` = concept, `+` = implemented, etc.)
   - Highlight notable patterns (under-capacity nodes, next priorities)
   - Summarize key metrics (total stories, completion percentage)

**DO NOT:**
- ❌ Show raw bash output and expect the user to see it (it gets truncated)
- ❌ Use `cat` or `echo` to display the tree (same truncation issue)
- ❌ Skip the visualization when output is too long

**Example workflow for "show story tree":**
```bash
# Step 1: Generate tree to temp file
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii > /tmp/tree.txt 2>&1
```
Then use Read tool to read `/tmp/tree.txt`, and present the contents in your response.

### Basic Usage

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

**Status symbols (ASCII):**
- concept=. approved=v rejected=x planned=o queued=@ active=O
- in-progress=D bugged=! implemented=+ ready=# deprecated=- infeasible=0

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

When database doesn't exist, follow the initialization procedure in **`lib/initialization.md`**.

This includes:
- Auto-detecting project name from `package.json` or `CLAUDE.md`
- Creating the `.claude/data/` directory
- Initializing schema and seeding the root node

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
- **lib/initialization.md**: Database initialization procedure (loaded only when needed)
- **lib/tree-analyzer.md**: SQL-based tree analysis algorithms
- **lib/pattern-matcher.md**: Git commit → story matching logic
- **lib/capacity-management.md**: Handling capacity issues
- **docs/rationale.md**: Design decisions, rationale, and version history
- **docs/tree-structure.md**: Detailed schema documentation
- **docs/migration-guide.md**: JSON to SQLite migration instructions
- **docs/common-mistakes.md**: Common pitfalls and how to avoid them
