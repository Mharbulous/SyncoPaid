# Handover 053: Story Tree Reorganization Capability

## Objective
Refactor the story-tree skill to add capabilities for reorganizing story nodes - finding misplaced nodes and moving them to more logical positions in the hierarchy by changing their parent and updating their IDs.

## Context Completed

### Issue Discovered
Stories 8.6 through 8.11 were incorrectly created as primary epics (children of root) but assigned decimal IDs instead of integer IDs:
- `8.6`, `8.7`, `8.8`, `8.9`, `8.10`, `8.11` should have been `16`, `17`, `18`, `19`, `20`, `21`

Additionally, 8.6-8.10 were "orphaned" - they existed in `story_nodes` but had no entries in `story_paths`, making them invisible to tree traversal.

### Fixes Applied
1. **Skill documentation updated:**
   - `.claude/skills/story-tree/SKILL.md` - Added "Story ID Format" section with rules
   - `.claude/skills/story-writing/SKILL.md` - Updated Step 4 with proper ID generation logic for root vs non-root parents
   - `.claude/skills/story-tree/references/common-mistakes.md` - Added mistake #7 about wrong ID formats

2. **Database corrected:**
   - Renamed `8.6`→`16`, `8.7`→`17`, `8.8`→`18`, `8.9`→`19`, `8.10`→`20`, `8.11`→`21`
   - Renamed children `8.11.1-7`→`21.1-7`
   - Added missing `story_paths` entries for orphaned nodes

## Next Task: Add Reorganization Commands

The story-tree skill needs commands for detecting and fixing structural issues.

### Proposed Commands

**1. Detect Misplaced Nodes**
```
"check story tree structure" or "validate story tree"
```
Should identify:
- Nodes with invalid ID format for their level (e.g., decimal ID at root level)
- Orphaned nodes (no `story_paths` entries)
- Nodes with ID prefix not matching parent ID (e.g., `3.5` as child of `8`)
- Missing self-path entries (depth=0)

**2. Move Story Node**
```
"move story [ID] to parent [NEW_PARENT_ID]"
```
Should:
- Validate the move is logical
- Generate new ID based on new parent
- Update `story_nodes.id`
- Update all `story_paths` entries (for node AND descendants)
- Update any child node IDs recursively
- Preserve all other fields

**3. Recompute Story Paths**
```
"rebuild story paths for [ID]"
```
Should:
- Delete all existing paths for the node and descendants
- Recompute based on current parent-child relationships
- Useful for fixing corrupted path data

### Implementation Details

#### ID Renaming Algorithm
```python
def rename_story(old_id: str, new_id: str, conn: sqlite3.Connection):
    """
    Rename a story and all its descendants.

    Steps:
    1. Find all descendants of old_id
    2. Compute new IDs for descendants (replace prefix)
    3. Use temp IDs to avoid conflicts
    4. Update story_nodes, story_paths, story_commits, vetting_decisions
    """
    # Get all descendant IDs
    descendants = conn.execute('''
        SELECT descendant_id FROM story_paths
        WHERE ancestor_id = ? AND depth > 0
        ORDER BY depth ASC
    ''', (old_id,)).fetchall()

    # Build rename map: old_id.X.Y → new_id.X.Y
    renames = {old_id: new_id}
    for (desc_id,) in descendants:
        if desc_id.startswith(old_id + '.'):
            suffix = desc_id[len(old_id):]
            renames[desc_id] = new_id + suffix

    # Execute renames (use temp IDs to avoid collisions)
    # ... (as implemented in the fix script)
```

#### Path Recomputation Algorithm
```python
def rebuild_paths(node_id: str, conn: sqlite3.Connection):
    """
    Rebuild story_paths for a node based on parent-child relationships.

    Uses recursive CTE to compute all ancestor paths.
    """
    # Delete existing paths
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (node_id,))

    # Insert self-path
    conn.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        VALUES (?, ?, 0)
    ''', (node_id, node_id))

    # Find parent from ID format
    if '.' in node_id:
        parent_id = node_id.rsplit('.', 1)[0]
    elif node_id.isdigit():
        parent_id = 'root'
    else:
        parent_id = None

    if parent_id:
        # Copy parent's ancestors and increment depth
        conn.execute('''
            INSERT INTO story_paths (ancestor_id, descendant_id, depth)
            SELECT ancestor_id, ?, depth + 1
            FROM story_paths WHERE descendant_id = ?
        ''', (node_id, parent_id))
```

### Location for New Code

Add to `.claude/skills/story-tree/utility/story_db_common.py`:
- `rename_story(old_id, new_id, conn)` - Rename story and descendants
- `rebuild_paths(node_id, conn)` - Recompute paths from parent-child
- `validate_tree_structure(conn)` - Find structural issues
- `move_story(story_id, new_parent_id, conn)` - Move node to new parent

### Workflow Addition

Add section to `.claude/skills/story-tree/SKILL.md`:
```markdown
## Tree Maintenance Commands

### Validate Structure
On "check story structure" or "validate story tree":
1. Run `validate_tree_structure()` to find issues
2. Report findings with suggested fixes

### Move Story
On "move story [ID] to [NEW_PARENT]":
1. Validate move is logical (not circular, parent exists)
2. Call `move_story()` to relocate
3. Show before/after tree snippets
```

## Acceptance Criteria

- [ ] `validate_tree_structure()` function identifies ID format violations
- [ ] `validate_tree_structure()` identifies orphaned nodes
- [ ] `rename_story()` correctly updates all references
- [ ] `move_story()` generates correct new IDs
- [ ] `rebuild_paths()` correctly recomputes closure table
- [ ] SKILL.md documents new commands
- [ ] common-mistakes.md updated with structural issues

## Files to Modify

1. `.claude/skills/story-tree/utility/story_db_common.py` - Add functions
2. `.claude/skills/story-tree/SKILL.md` - Add maintenance commands section
3. `.claude/skills/story-tree/references/sql-queries.md` - Add validation queries
4. `.claude/skills/story-tree/references/common-mistakes.md` - Add structural mistake patterns

## Notes

- Always use Python sqlite3, never CLI
- Foreign keys should be disabled during bulk operations
- Use temporary IDs when renaming to avoid conflicts
- The closure table pattern means ALL ancestor paths must be updated, not just direct parent
