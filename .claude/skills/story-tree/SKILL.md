---
name: story-tree
description: Use when user says "update story tree", "show story tree", "show me a map", "story map", "tree diagram", "show stories", "view stories", "list stories", or asks for story visualization or tree status - autonomously maintains hierarchical story backlog by analyzing git commits, identifying under-capacity nodes, and coordinating story generation to fill gaps. Works with SQLite database using closure table pattern, prioritizes shallower nodes first, and tracks implementation status through commit analysis.
disable-model-invocation: true
---

# Story Tree - Autonomous Hierarchical Backlog Manager

Self-managing tree of user stories with capacity-based story generation.

**Database:** `.claude/data/story-tree.db`
**Schema:** `references/schema.sql`

**Design rationale:** If instructions seem counter-intuitive, consult `references/rationales.md`.

## Story ID Format

**Critical:** IDs follow a strict hierarchical format:

| Level | Parent | ID Format | Examples |
|-------|--------|-----------|----------|
| Root | None | `root` | `root` |
| Level 1 (Primary Epics) | `root` | Plain integer | `1`, `2`, `15`, `16` |
| Level 2+ | Any non-root | `[parent].[N]` | `1.1`, `8.4`, `15.2.1` |

**Common mistake:** Creating root children with decimal IDs like `8.6` or `root.1`. Primary epics MUST have plain integer IDs.

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
- `hold_reason IS NOT NULL` (queued/pending/blocked/etc)
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

### Stage (10 values) - Linear workflow position
| Stage | Description |
|-------|-------------|
| concept | Initial idea, not yet approved |
| approved | Ready to plan |
| planned | Implementation plan exists, dependencies verified |
| active | Currently being worked on |
| reviewing | Under review/testing |
| verifying | Awaiting post-execution verification |
| implemented | Code complete, verified, not released |
| ready | Tested, ready for release |
| polish | Minor refinements |
| released | Deployed to production |

### Hold Reason (8 values + NULL) - Why work is stopped
| Hold | Description |
|------|-------------|
| NULL | Not held, work can proceed |
| ⏳ queued | Waiting for automated processing (algorithm hasn't run yet) |
| ❓ pending | Awaiting human decision (algorithm ran but can't decide) |
| ⊗ blocked | External dependency |
| ⏸ paused | Execution blocked by critical issue |
| ⚠ broken | Something wrong with story definition |
| ◇ polish | Needs refinement before proceeding |
| ⚡ conflict | Inconsistent with another story, needs human resolution |
| ? wishlist | Indefinite hold, maybe someday (can be revived when priorities change) |

### Disposition (6 values + NULL) - Terminal state
| Disposition | Description | Stage Required |
|-------------|-------------|----------------|
| NULL | Active in pipeline | Any |
| rejected | Human decided not to implement (indicates non-goal) | Any (preserved) |
| infeasible | Cannot implement | Any (preserved) |
| duplicative | Algorithm detected duplicate/overlap with existing (not a goal signal) | Any (preserved) |
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

## Shared Database Utilities

Python scripts that interact with the story-tree database should import from the shared utility module:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import (
    DB_PATH,                    # '.claude/data/story-tree.db'
    MERGEABLE_STATUSES,         # {'concept', 'wishlist', 'polish'} - concept=stage, others=hold_reason
    BLOCK_STATUSES,             # {'rejected', 'infeasible', 'duplicative', 'broken', ...}
    get_connection,             # Get SQLite connection
    make_pair_key,              # Canonical pair key for caching
    get_story_version,          # Get story version number
    compute_effective_status,   # COALESCE(disposition, hold_reason, stage)
    delete_story,               # Cascade delete from story_nodes + story_paths
    reject_concept,             # Human rejection (disposition='rejected', goal signal)
    duplicative_concept,        # Algorithm duplicate (disposition='duplicative', no signal)
    conflict_concept,           # Inconsistent stories (hold_reason='conflict', needs resolution)
    block_concept,              # Set hold_reason='blocked' with note
    defer_concept,              # Set hold_reason='pending' with note
    merge_concepts,             # Merge two stories into one
    # Tree reorganization functions
    validate_tree_structure,    # Find structural issues in tree
    rename_story,               # Rename story and all descendants
    rebuild_paths,              # Recompute paths for a node
    rebuild_paths_recursive,    # Recompute paths for node and descendants
    move_story,                 # Move story to new parent
    get_next_child_id,          # Get next available child ID
    get_expected_parent_id,     # Determine expected parent from ID format
)
```

**Location:** `.claude/skills/story-tree/utility/story_db_common.py`

This ensures DRY principles - all story-related skills use the same database operations.

## Tree Maintenance Commands

Commands for detecting and fixing structural issues in the story tree.

### Validate Structure

On "check story structure", "validate story tree", or "find tree issues":

1. Run `validate_tree_structure(conn)` to identify issues:
   - **invalid_root_children**: Decimal IDs at root level (e.g., `8.6` should be `16`)
   - **orphaned_nodes**: Stories missing from `story_paths` (invisible to tree)
   - **missing_self_paths**: Stories without depth=0 self-reference
   - **parent_mismatch**: Story ID prefix doesn't match actual parent
   - **invalid_id_format**: Malformed IDs (non-numeric parts)

2. Report findings with suggested fixes:
```python
python -c "
import sys, os
sys.path.insert(0, '.claude/skills/story-tree/utility')
from story_db_common import get_connection, validate_tree_structure

conn = get_connection()
issues = validate_tree_structure(conn)
for category, items in issues.items():
    if items:
        print(f'\n{category}:')
        for item in items:
            print(f'  - {item}')
conn.close()
"
```

### Move Story

On "move story [ID] to [NEW_PARENT]" or "relocate story [ID] under [PARENT]":

1. Validate move is logical:
   - Story exists
   - New parent exists
   - Not circular (can't move to self or descendant)

2. Call `move_story(conn, story_id, new_parent_id)`:
   - Generates appropriate new ID (integer for root, decimal for others)
   - Renames story and all descendants
   - Rebuilds closure table paths

3. Show before/after:
```python
python -c "
import sys, os
sys.path.insert(0, '.claude/skills/story-tree/utility')
from story_db_common import get_connection, move_story

conn = get_connection()
try:
    new_id = move_story(conn, 'OLD_ID', 'NEW_PARENT')
    conn.commit()
    print(f'Moved: OLD_ID -> {new_id}')
except ValueError as e:
    print(f'Error: {e}')
conn.close()
"
```

### Rebuild Paths

On "rebuild story paths for [ID]" or "fix paths for [ID]":

1. Call `rebuild_paths_recursive(conn, node_id)` to recompute closure table
2. Useful for fixing corrupted path data after manual edits

```python
python -c "
import sys, os
sys.path.insert(0, '.claude/skills/story-tree/utility')
from story_db_common import get_connection, rebuild_paths_recursive

conn = get_connection()
count = rebuild_paths_recursive(conn, 'STORY_ID')
conn.commit()
print(f'Rebuilt paths for {count} nodes')
conn.close()
"
```

### Rename Story

On "rename story [OLD_ID] to [NEW_ID]":

1. Call `rename_story(conn, old_id, new_id)` to rename with descendants
2. Updates `story_nodes`, `story_paths`, `story_commits`, `vetting_decisions`

```python
python -c "
import sys, os
sys.path.insert(0, '.claude/skills/story-tree/utility')
from story_db_common import get_connection, rename_story

conn = get_connection()
conn.execute('PRAGMA foreign_keys = OFF')  # Disable during bulk rename
renames = rename_story(conn, 'OLD_ID', 'NEW_ID')
conn.execute('PRAGMA foreign_keys = ON')
conn.commit()
for old, new in renames:
    print(f'  {old} -> {new}')
conn.close()
"
```

## References

- `references/schema.sql` - Database schema
- `references/sql-queries.md` - Query patterns
- `references/rationales.md` - Design decisions
- `utility/story_db_common.py` - Shared database utilities
- `.claude/skills/story-writing/SKILL.md` - Story generation
