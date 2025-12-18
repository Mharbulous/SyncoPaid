# Handover: Story Tree Status Expansion & Database Reset

## Task
Delete `.claude/data/story-tree.db` and test database initialization with the updated schema.

## What Changed This Session

### 1. tree-view.py UX improvements
- Node IDs now shown by default (use `--hide-ids` to suppress)
- Status symbols now shown by default (use `--hide-status` to suppress)
- Changed `--show-status` → `--hide-status` (inverted default)

### 2. Expanded status types (6 → 12)

```
concept → approved → planned → pending → active → in-progress → implemented → ready
              ↓                                        ↓              ↓
          rejected                                  bugged      deprecated
                                                      ↓
                                                 infeasible
```

| Status | Unicode | ASCII | Description |
|--------|---------|-------|-------------|
| concept | · | . | Idea, not yet approved |
| approved | ✓ | v | Human approved, not planned |
| rejected | ✗ | x | Human rejected |
| planned | ○ | o | Implementation plan created |
| pending | ◎ | @ | Plan ready, dependencies met |
| active | ● | O | Currently being worked on |
| in-progress | ◐ | D | Partially complete |
| bugged | ⚠ | ! | Needs debugging |
| implemented | ★ | + | Complete/done |
| ready | ✔ | # | Production ready, tested |
| deprecated | ⊘ | - | No longer relevant |
| infeasible | ∅ | 0 | Couldn't build it |

## Files Modified
- `.claude/skills/story-tree/tree-view.py` - Status symbols, defaults, CLI args
- `.claude/skills/story-tree/schema.sql` - CHECK constraint
- `.claude/skills/story-tree/SKILL.md` - Status docs, CHECK constraint
- `.claude/skills/story-tree/docs/tree-structure.md` - Status table, validation query

## Key Files
- `.claude/skills/story-tree/SKILL.md` - Main skill definition, has initialization SQL
- `.claude/skills/story-tree/schema.sql` - Canonical schema
- `.claude/data/story-tree.db` - Database to delete (contains old CHECK constraint)

## Test Plan
1. Delete `.claude/data/story-tree.db`
2. Run `python .claude/skills/story-tree/tree-view.py` - should fail gracefully (no db)
3. Initialize per SKILL.md instructions (lines 157-169)
4. Verify tree-view.py shows root node with new status symbols
5. Test adding a node with new status (e.g., `approved`)

## Notes
- Database CHECK constraint won't auto-update on existing DBs - must recreate
- Root node uses `active` status (special case)
