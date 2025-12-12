# Handover: Story Tree Skill Review and Testing

## Objective

Full review of the story-tree skill design after recent changes. Build tests to verify correctness.

## Critical Bug Found

**Table name mismatch:** `tree-view.py` queries `story_tree` table, but `schema.sql` creates `story_paths`.

```python
# tree-view.py line 179-186
JOIN story_tree st ON s.id = st.descendant_id
```

```sql
# schema.sql line 22-27
CREATE TABLE IF NOT EXISTS story_paths (...)
```

Fix this first before testing.

## Recent Changes (This Session)

1. Added `tree-view.py` integration to SKILL.md (new "Tree Visualization Script" section)
2. Simplified `story-tree-diagram.md` from 225-line manual diagram to 48-line reference doc
3. Added tree-view.py references to `lib/tree-analyzer.md`

## Key Files

| File | Purpose | Notes |
|------|---------|-------|
| `SKILL.md` | Main skill instructions | Recently updated |
| `schema.sql` | Database schema | Uses `story_paths` table |
| `tree-view.py` | ASCII visualization CLI | Uses wrong table name `story_tree` |
| `lib/tree-analyzer.md` | SQL query reference | May have same table name issue |
| `.claude/data/story-tree.db` | Actual database | Check what table name exists |

## Files to Review for Table Name Consistency

Check all files for `story_tree` vs `story_paths`:
- `tree-view.py` - uses `story_tree`
- `lib/tree-analyzer.md` - likely has `story_tree`
- `schema.sql` - uses `story_paths`
- `SKILL.md` - uses `story_paths` in schema docs

## Red Herrings

- `story-tree.json.backup` - Old JSON format, deprecated after SQLite migration
- `docs/migration-guide.md` - For JSON→SQLite migration, not relevant to review
- `lib/*.md` files - Prompt libraries, not executable code

## Testing Approach

1. **Schema consistency:** Verify all SQL references use correct table name
2. **tree-view.py:** Test each command option from SKILL.md examples
3. **Database integrity:** Verify closure table invariants (self-references, depth calculations)
4. **Priority algorithm:** Test that under-capacity detection works correctly

## Test Commands (After Fixing Table Name)

```bash
# Verify database exists and has correct schema
sqlite3 .claude/data/story-tree.db ".schema"

# Test tree-view.py options
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii
python .claude/skills/story-tree/tree-view.py --root 1.1 --depth 2
python .claude/skills/story-tree/tree-view.py --format markdown

# Test SQL queries from schema.sql comments
sqlite3 .claude/data/story-tree.db "SELECT COUNT(*) FROM story_nodes;"
```

## No Failed Approaches

This is a new review task, no prior attempts.
