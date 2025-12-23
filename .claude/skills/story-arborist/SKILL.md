---
name: story-arborist
description: Analyze, diagnose, and reorganize story tree structure. Use when user says "check tree health", "find orphans", "move story", "rename story", "fix tree structure", "reparent stories", "validate tree", or when structural issues are suspected in story-tree.db. Focuses Claude on diagnosis while delegating mechanical operations to deterministic scripts.
---

# Story Arborist - Tree Structure Analysis and Reorganization

Diagnose structural issues and reorganize story-tree.db nodes using deterministic scripts.

**Database:** `.claude/data/story-tree.db`
**Scripts:** `.claude/skills/story-arborist/scripts/`

## Design Philosophy

**Analysis is hard; execution is mechanical.** This skill:
1. Focuses Claude's context on analyzing tree structure and identifying issues
2. Delegates all mechanical operations (moves, renames, path rebuilds) to Python scripts
3. Scripts run without loading into context, preserving budget for diagnosis

## Quick Reference

| Task | Script |
|------|--------|
| Full health check | `python scripts/tree_health.py` |
| Validate structure | `python scripts/validate_tree.py` |
| List orphans | `python scripts/list_orphans.py` |
| Fix orphans | `python scripts/fix_orphans.py` |
| Move node | `python scripts/move_node.py <id> <parent>` |
| Rename node | `python scripts/rename_node.py <old> <new>` |
| Rebuild paths | `python scripts/rebuild_paths.py <id>` |
| Bulk reparent | `python scripts/bulk_reparent.py <parent> <id1> <id2>...` |

All scripts support `--dry-run` for preview.

## Workflow: Diagnose Then Fix

### Step 1: Run Health Check

```bash
python .claude/skills/story-arborist/scripts/tree_health.py
```

Reports: statistics, stage/hold/disposition distribution, structural issues.

### Step 2: Analyze Issues

For each issue category, determine root cause:

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| **orphaned_nodes** | Node created without path entries | `fix_orphans.py` |
| **invalid_root_children** | Decimal ID at root level (e.g., `8.6` should be `16`) | `move_node.py` or `rename_node.py` |
| **missing_self_paths** | Corrupted closure table | `rebuild_paths.py --recursive` |
| **parent_mismatch** | ID prefix doesn't match actual parent | `move_node.py` |
| **invalid_id_format** | Non-numeric parts in ID | Manual investigation |

### Step 3: Apply Fixes

Always use `--dry-run` first:

```bash
# Preview fix
python .claude/skills/story-arborist/scripts/move_node.py 8.6 root --dry-run

# Apply fix
python .claude/skills/story-arborist/scripts/move_node.py 8.6 root
```

### Step 4: Verify

```bash
python .claude/skills/story-arborist/scripts/validate_tree.py
```

## Common Scenarios

### Misplaced Root Children

**Symptom:** Decimal IDs like `8.6`, `8.7` appearing as direct children of root.

**Diagnosis:** These should be integer IDs (`16`, `17`, etc.) since root children must be primary epics.

**Fix options:**
1. **Move to root (auto-assigns integer ID):**
   ```bash
   python scripts/move_node.py 8.6 root
   ```
2. **Rename directly:**
   ```bash
   python scripts/rename_node.py 8.6 16
   ```

### Orphaned Nodes

**Symptom:** Stories exist in `story_nodes` but are invisible to tree traversal.

**Diagnosis:** Missing `story_paths` entries.

**Fix:**
```bash
python scripts/fix_orphans.py
```

### Bulk Reorganization

**Symptom:** Multiple nodes need to move to same parent.

**Fix:**
```bash
python scripts/bulk_reparent.py 15 1.2 1.3 1.4
```

### Corrupted Paths

**Symptom:** `parent_mismatch` or `missing_self_paths` errors.

**Fix:**
```bash
python scripts/rebuild_paths.py root --recursive
```

## ID Format Rules

| Level | Format | Examples |
|-------|--------|----------|
| Root | `root` | `root` |
| Primary epics | Integer | `1`, `15`, `23` |
| Children | `parent.N` | `1.2`, `15.3.1` |

**Critical:** Primary epics (root children) MUST have plain integer IDs, never decimal.

## Script Details

### tree_health.py
Full diagnostic report with statistics and structural issues.
- `--json`: Output machine-readable JSON

### validate_tree.py
Structural validation only, no statistics.
- `--json`: Output as JSON

### list_orphans.py
List orphaned nodes.
- `--ids-only`: Output IDs only (for scripting)

### fix_orphans.py
Auto-fix all orphaned nodes by rebuilding paths.
- `--dry-run`: Preview without changes

### move_node.py
Move node to new parent with auto-generated ID.
- `--dry-run`: Preview the move

### rename_node.py
Rename node and all descendants.
- `--dry-run`: Preview renames

### rebuild_paths.py
Reconstruct closure table entries.
- `--recursive`: Include descendants
- `--dry-run`: Preview

### bulk_reparent.py
Move multiple nodes to same parent.
- `--dry-run`: Preview moves

## Database Utilities

Scripts use shared functions from `story-tree/utility/story_db_common.py`:
- `validate_tree_structure(conn)` - Find issues
- `rename_story(conn, old_id, new_id)` - Rename with descendants
- `rebuild_paths(conn, node_id)` - Single node
- `rebuild_paths_recursive(conn, node_id)` - Node and descendants
- `move_story(conn, story_id, new_parent_id)` - Move with validation
- `get_next_child_id(conn, parent_id)` - Next available child ID
