---
name: story-tree
description: Use when user says "generate stories", "brainstorm features", "update story tree", "what should we build", "show story tree", "show me a map", "story map", "tree diagram", "show stories", "view stories", "list stories", or asks for feature ideas or story visualization - autonomously maintains hierarchical story backlog by analyzing git commits, identifying under-capacity nodes, and generating evidence-based stories to fill gaps. Works with SQLite database using closure table pattern, prioritizes shallower nodes first, and tracks implementation status through commit analysis.
---

# Story Tree - Autonomous Hierarchical Backlog Manager

## Purpose

Maintain a **self-managing tree of user stories** where:
- Each node represents a story at some level of granularity
- Each node has a **capacity** (target number of child nodes)
- The skill autonomously identifies **under-capacity nodes** and generates stories to fill them
- Git commits are analyzed to mark stories as **implemented**
- Higher-level nodes are prioritized when under capacity

**Design rationale:** If instructions seem counter-intuitive, consult `references/rationales.md` before changing approach.

## When NOT to Use

- Creating 1-3 specific stories manually
- Non-hierarchical backlogs
- Projects without git history
- Real-time task tracking
- Detailed implementation planning (use `superpowers:writing-plans`)
- Non-software projects

## Storage

**Database:** `.claude/data/story-tree.db`
**Schema:** `references/schema.sql`

Ensure `.gitignore` includes: `*.db` with exception `!.claude/data/story-tree.db`

## Autonomous Operation

When user says "update story tree" or "generate stories":
1. Run complete workflow (Steps 1-7) without asking permission
2. Generate stories based on git analysis and priority algorithm
3. Output complete report when finished
4. Ask for clarification ONLY when: over-capacity detected, multiple equal priorities, or ambiguous git history

### Auto-Update on Staleness

On ANY invocation, check `lastUpdated` in metadata. If >3 days old, run full update first.

## Workflow Steps

### Step 1: Initialize/Load Database

If `.claude/data/story-tree.db` doesn't exist:

```bash
mkdir -p .claude/data

# Get project name from package.json or default
PROJECT_NAME=$(python -c "import json; print(json.load(open('package.json')).get('name', 'Software Project'))" 2>/dev/null || echo "Software Project")

sqlite3 .claude/data/story-tree.db < references/schema.sql

sqlite3 .claude/data/story-tree.db "
INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
VALUES ('root', '$PROJECT_NAME', 'Project root', 'active', datetime('now'), datetime('now'));

INSERT INTO story_paths (ancestor_id, descendant_id, depth) VALUES ('root', 'root', 0);

INSERT INTO metadata (key, value) VALUES ('version', '2.4.0');
INSERT INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));
"
```

### Step 2: Analyze Git Commits

Use incremental analysis from checkpoint:

```bash
LAST_COMMIT=$(sqlite3 .claude/data/story-tree.db "SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit';")

if [ -z "$LAST_COMMIT" ] || ! git cat-file -t "$LAST_COMMIT" &>/dev/null; then
    git log --since="30 days ago" --pretty=format:"%h|%ai|%s" --no-merges
else
    git log "$LAST_COMMIT"..HEAD --pretty=format:"%h|%ai|%s" --no-merges
fi
```

Match commits to stories using keyword similarity (see `references/sql-queries.md#pattern-matching`).

### Step 3: Identify Priority Target

**Excluded statuses:** `concept`, `rejected`, `deprecated`, `infeasible`, `bugged`

**Priority algorithm** - find under-capacity nodes, shallower first:

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
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

**Dynamic capacity:** `effective_capacity = capacity_override OR (3 + implemented/ready children)`

### Step 4: Generate Stories (Max 3 per node)

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

New nodes start with `status: 'concept'`. When user explicitly requests "generate stories for [node-id]", create with `status: 'approved'` instead.

### Step 5: Insert Stories

```sql
-- Insert story (capacity NULL = dynamic)
INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
VALUES (:new_id, :title, :description, 'concept', datetime('now'), datetime('now'));

-- Populate closure table
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, :new_id, depth + 1
FROM story_paths WHERE descendant_id = :parent_id
UNION ALL SELECT :new_id, :new_id, 0;
```

### Step 6: Update Metadata

```sql
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', :newest_commit);
```

### Step 7: Output Report

```markdown
# Story Tree Update Report
Generated: [ISO timestamp]

## Current Tree Status
- Total nodes: [N]
- Implemented: [N] ([%]%)
- In progress: [N] ([%]%)

## Git Commits Analyzed
[List matched commits]

## Priority Target
**Node**: [ID] "[Title]" - Level [N], [children]/[capacity]

## Generated Stories
[Full story format for each]

## Tree Visualization
[Run tree-view.py and present output]
```

## Tree Visualization

**Critical:** Bash output gets truncated. Always save to file and read:

```bash
python scripts/tree-view.py --show-capacity --force-ascii > /tmp/tree.txt
```

Then read `/tmp/tree.txt` and present in response as code block.

**Status symbols (ASCII):**
| Status | Symbol |
|--------|--------|
| concept | `.` |
| approved | `v` |
| planned | `o` |
| in-progress | `D` |
| implemented | `+` |
| ready | `#` |
| deprecated | `-` |

## User Commands

| Command | Action |
|---------|--------|
| "Update story tree" | Run full workflow |
| "Show story tree" | Visualize current tree |
| "Tree status" | Show metrics only |
| "Set capacity for [id] to [N]" | Adjust capacity |
| "Mark [id] as [status]" | Change status |
| "Generate stories for [id]" | Force generation for node |
| "Initialize story tree" | Create new database |

## Quality Checks

Before outputting stories, verify:
- [ ] Each story has clear basis in commits or gap analysis
- [ ] Stories are specific and actionable
- [ ] Acceptance criteria are testable
- [ ] No duplicates
- [ ] User story format complete

## References

- **`references/schema.sql`** - Database schema (source of truth)
- **`references/sql-queries.md`** - All SQL query patterns
- **`references/common-mistakes.md`** - Error prevention
- **`references/rationales.md`** - Design decisions
