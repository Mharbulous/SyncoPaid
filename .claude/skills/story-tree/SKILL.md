---
name: story-tree
description: Use when user says "update story tree", "show story tree", "show me a map", "story map", "tree diagram", "show stories", "view stories", "list stories", or asks for story visualization or tree status - autonomously maintains hierarchical story backlog by analyzing git commits, identifying under-capacity nodes, and coordinating story generation to fill gaps. Works with SQLite database using closure table pattern, prioritizes shallower nodes first, and tracks implementation status through commit analysis.
---

# Story Tree - Autonomous Hierarchical Backlog Manager

Self-managing tree of user stories with capacity-based story generation.

**Database:** `.claude/data/story-tree.db`
**Schema:** `references/schema.sql`

**Design rationale:** If instructions seem counter-intuitive, consult `references/rationales.md`.

## Environment Requirements

**Critical:** The `sqlite3` CLI is NOT available. Always use Python's sqlite3 module:

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('YOUR SQL HERE')
print(cursor.fetchall())
conn.close()
"
```

**Script path:** `.claude/skills/story-tree/scripts/tree-view.py` (NOT project root `scripts/`)

## Autonomous Operation

**On "update story tree":** Run Steps 1-7 without permission, invoke story-writing for priority target, output report. Ask clarification ONLY for: over-capacity, multiple equal priorities, or ambiguous git history.

**On "generate stories":** Delegate to story-writing skill.

**Auto-update:** On ANY invocation, if `lastUpdated` metadata >3 days old, run full update first.

## Workflow

### Step 1: Initialize Database

If `.claude/data/story-tree.db` doesn't exist, create directory and execute `references/schema.sql` via Python sqlite3, then insert root node and metadata.

### Step 2: Analyze Git Commits

Use incremental analysis from `lastAnalyzedCommit` checkpoint:

```python
python -c "
import sqlite3, subprocess
conn = sqlite3.connect('.claude/data/story-tree.db')
row = conn.execute(\"SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit'\").fetchone()
last_commit = row[0] if row else None
conn.close()

if last_commit:
    result = subprocess.run(['git', 'cat-file', '-t', last_commit], capture_output=True)
    if result.returncode != 0: last_commit = None

cmd = ['git', 'log', f'{last_commit}..HEAD' if last_commit else '--since=30 days ago',
       '--pretty=format:%h|%ai|%s', '--no-merges']
print(subprocess.run(cmd, capture_output=True, text=True).stdout)
"
```

### Step 3: Identify Priority Target

**Excluded from generation:** Stories where:
- `stage = 'concept'` (not yet approved)
- `hold_reason IS NOT NULL` (blocked/pending/etc)
- `disposition IS NOT NULL` (rejected/archived/etc)

**Priority algorithm** (shallower under-capacity nodes first):

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
         JOIN story_nodes child ON sp.descendant_id = child.id
         WHERE sp.ancestor_id = s.id AND sp.depth = 1
         AND child.stage IN ('implemented', 'ready', 'released')
         AND child.disposition IS NULL)) as effective_capacity
FROM story_nodes s
WHERE s.stage != 'concept'
  AND s.hold_reason IS NULL
  AND s.disposition IS NULL
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
      COALESCE(s.capacity, 3 + (...))
ORDER BY node_depth ASC
LIMIT 1;
```

**Dynamic capacity:** `effective_capacity = capacity_override OR (3 + implemented/ready children)`

### Step 4: Generate Stories

Invoke `story-writing` skill for priority target node. New stories get `stage: 'concept'` (unless user explicitly requested `approved`).

### Step 5: Update Metadata

```sql
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));
INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', :newest_commit);
```

### Step 6: Output Report

Include: tree status metrics, analyzed commits, priority target, generated stories, tree visualization.

## Tree Visualization

```bash
python .claude/skills/story-tree/scripts/tree-view.py --show-capacity
```

Use `--force-ascii` only if Unicode fails.

## Three-Field Workflow System (v4.0)

Stories use three orthogonal dimensions instead of a single status:

### Stage (11 values) - Linear workflow position
| Stage | Description |
|-------|-------------|
| concept | Initial idea, not yet approved |
| approved | Ready to plan |
| planned | Implementation plan exists |
| queued | In backlog, ready to start |
| active | Currently being worked on |
| reviewing | Under review/testing |
| verifying | Awaiting post-execution verification |
| implemented | Code complete, verified, not released |
| ready | Tested, ready for release |
| polish | Minor refinements |
| released | Deployed to production |

### Hold Reason (5 values + NULL) - Why work is stopped
| Hold | Description | Valid Stages |
|------|-------------|--------------|
| NULL | Not held, work can proceed | Any |
| pending | Awaiting human decision | Any |
| blocked | External dependency | Any |
| paused | Execution blocked by critical issue | active only |
| broken | Something wrong with story definition | concept only |
| refine | Needs more detail | concept only |

### Disposition (6 values + NULL) - Terminal state
| Disposition | Description | Stage Required |
|-------------|-------------|----------------|
| NULL | Active in pipeline | Any |
| rejected | Will not implement | Any (preserved) |
| infeasible | Cannot implement | Any (preserved) |
| wishlist | Maybe someday | Any (preserved) |
| legacy | Old but functional | released |
| deprecated | Being phased out | released |
| archived | No longer relevant | Any (preserved) |

### Human Review Flag
- `human_review = 1` when story needs human attention
- Typically TRUE when `hold_reason IS NOT NULL`

### Key Rules
- **Cannot have both** hold_reason AND disposition (mutually exclusive)
- Stage is **preserved** when held or disposed (know where to resume)
- Query by dimension for clearer intent

## References

- `references/schema.sql` - Database schema
- `references/sql-queries.md` - Query patterns
- `references/rationales.md` - Design decisions
- `.claude/skills/story-writing/SKILL.md` - Story generation
