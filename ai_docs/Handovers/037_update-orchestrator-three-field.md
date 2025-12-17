# Handover: Update GitHub Actions Workflows for Three-Field System

## Task

Update GitHub Actions workflows and helper scripts to query using three-field system (`stage`/`hold_reason`/`disposition`) instead of deprecated `status` column.

## Context

**Migration Complete:** Database migrated to three-field system (commit f45c6df).

**Why Update Now:**
- Status column kept for backward compatibility via sync trigger
- Workflows still functional but semantically incorrect
- Prepares for eventual status column removal (handover 036)
- Queries should reflect current data model (stage preserved when held/disposed)

**What Works vs What's Semantically Wrong:**

```python
# WORKS (trigger syncs status from three-field):
WHERE status="approved"

# CORRECT (semantic three-field query):
WHERE stage='approved' AND hold_reason IS NULL AND disposition IS NULL

# Why correct matters:
# - 'approved' status = stage='approved' + NOT held + NOT disposed
# - Three-field query is explicit about all conditions
# - Prepares for status column removal
```

## Files to Update

| File | Line | Current Query | Issue |
|------|------|--------------|-------|
| `.github\workflows\story-tree-orchestrator.yml` | 137 | `status=\"approved\"` | Should check stage + not held/disposed |
| `.github\workflows\plan-stories.yml` | 52 | `status=\"approved\"` | Same as above |
| `.claude\scripts\insert_story.py` | 22 | `status` column | Should use `stage` column |

## Already Updated (Red Herrings)

✅ **Don't touch these:**
- `.claude\scripts\story_workflow.py` - Already uses three-field (lines 55-72)
- Skill SKILL.md files - Being updated in handover 035
- Database schema - Migration complete, trigger maintains status

## Implementation

### 1. Update story-tree-orchestrator.yml

**Line 137 - Replace inline Python query:**

```diff
-            approved_info=$(python3 -c "import sqlite3; conn = sqlite3.connect('.claude/data/story-tree.db'); rows = conn.execute('SELECT id, title FROM story_nodes WHERE status=\"approved\" ORDER BY id LIMIT 1').fetchall(); print(f'{rows[0][0]}|{rows[0][1][:50]}' if rows else 'NONE')" 2>/dev/null || echo "NONE")
+            approved_info=$(python3 -c "import sqlite3; conn = sqlite3.connect('.claude/data/story-tree.db'); rows = conn.execute('SELECT id, title FROM story_nodes WHERE stage=\"approved\" AND hold_reason IS NULL AND disposition IS NULL ORDER BY id LIMIT 1').fetchall(); print(f'{rows[0][0]}|{rows[0][1][:50]}' if rows else 'NONE')" 2>/dev/null || echo "NONE")
```

**Why three conditions:**
- `stage='approved'` - Story is in approved stage
- `hold_reason IS NULL` - Not blocked/pending/paused
- `disposition IS NULL` - Not rejected/archived/wishlist

An "approved" story that's been blocked should have `stage='approved'` + `hold_reason='blocked'` - shouldn't be planned until unblocked.

### 2. Update plan-stories.yml

**Line 52 - Replace inline Python query:**

```diff
-            count = conn.execute('SELECT COUNT(*) FROM story_nodes WHERE status=\"approved\"').fetchone()[0]
+            count = conn.execute('SELECT COUNT(*) FROM story_nodes WHERE stage=\"approved\" AND hold_reason IS NULL AND disposition IS NULL').fetchone()[0]
```

### 3. Update insert_story.py

**Line 22 - Replace status column with stage:**

```diff
     cursor.execute('''
-        INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
-        VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
+        INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
+        VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
     ''', (story_id, title, description))
```

**Note:** New stories default to `stage='concept'`, `hold_reason=NULL`, `disposition=NULL`, `human_review=0`

## Verification

### Test Query Equivalence

Before/after should return same results (while status column exists):

```bash
# Before migration (old query)
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
old = conn.execute('SELECT id FROM story_nodes WHERE status=\"approved\" ORDER BY id').fetchall()
new = conn.execute('SELECT id FROM story_nodes WHERE stage=\"approved\" AND hold_reason IS NULL AND disposition IS NULL ORDER BY id').fetchall()
assert old == new, f'Mismatch: {old} vs {new}'
print('✓ Queries return identical results')
conn.close()
"
```

Expected: Identical results (status trigger keeps them in sync)

### Test Insert Script

```bash
# Create test story
python .claude/scripts/insert_story.py "test-id" "root" "Test Story" "Test description"

# Verify three-field defaults
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
row = conn.execute('SELECT stage, hold_reason, disposition, human_review FROM story_nodes WHERE id=\"test-id\"').fetchone()
assert row == ('concept', None, None, 0), f'Unexpected values: {row}'
print('✓ New story has correct three-field defaults')

# Cleanup
conn.execute('DELETE FROM story_nodes WHERE id=\"test-id\"')
conn.execute('DELETE FROM story_paths WHERE descendant_id=\"test-id\"')
conn.commit()
conn.close()
print('✓ Test story cleaned up')
"
```

### Test Workflow Locally

```bash
# Simulate orchestrator approved query
python3 -c "import sqlite3; conn = sqlite3.connect('.claude/data/story-tree.db'); rows = conn.execute('SELECT id, title FROM story_nodes WHERE stage=\"approved\" AND hold_reason IS NULL AND disposition IS NULL ORDER BY id LIMIT 1').fetchall(); print(f'{rows[0][0]}|{rows[0][1][:50]}' if rows else 'NONE')"

# Should output story ID|title or NONE if no approved stories
```

## Understanding Three-Field Queries

### Common Query Patterns

```sql
-- Active pipeline stories (not held, not disposed)
WHERE hold_reason IS NULL AND disposition IS NULL

-- Held stories (work stopped, but stage preserved)
WHERE hold_reason IS NOT NULL

-- Stories needing human review
WHERE human_review = 1

-- Approved AND ready to work (not blocked)
WHERE stage='approved' AND hold_reason IS NULL AND disposition IS NULL

-- Blocked approved story (keep stage, add hold)
-- stage='approved', hold_reason='blocked', disposition=NULL

-- Rejected concept (keep stage, add disposition)
-- stage='concept', hold_reason=NULL, disposition='rejected'
```

### Why NOT Just `stage='approved'`?

**Scenario:** User approves story, then discovers dependency. Sets `hold_reason='blocked'`.

```sql
-- Wrong query (returns blocked stories too):
WHERE stage='approved'
-- Returns: [story-1 (approved, not held), story-2 (approved, blocked)]

-- Correct query (excludes held stories):
WHERE stage='approved' AND hold_reason IS NULL AND disposition IS NULL
-- Returns: [story-1 (approved, not held)]
```

Stage preserves WHERE in pipeline, hold/disposition indicate WHY work can't proceed.

## Reference Documentation

**Three-field system:**
- `.claude\skills\story-tree\references\schema.sql` lines 12-48 (field definitions)
- `.claude\skills\story-tree\references\schema.sql` lines 139-174 (design reference)
- `.claude\data\plans\meta-workflow-three-field.json` (design rationale)

**Migration script (for understanding mappings):**
- `.claude\skills\story-tree\scripts\migrate_to_three_field.py` lines 30-69

**Already-updated helper:**
- `.claude\scripts\story_workflow.py` lines 55-72 (correct three-field query example)

## Why This Matters

1. **Semantic Correctness** - Queries express actual business rules (approved + not held)
2. **Prepares for Cleanup** - When status column removed (handover 036), workflows keep working
3. **Documentation Alignment** - Code matches schema documentation
4. **Query Performance** - Uses semantic indexes (idx_active_pipeline, idx_held_stories)

## Rollback Plan

If workflows fail after changes:

```bash
# Revert workflow files
git checkout HEAD~1 -- .github/workflows/story-tree-orchestrator.yml
git checkout HEAD~1 -- .github/workflows/plan-stories.yml
git checkout HEAD~1 -- .claude/scripts/insert_story.py

# Test with old queries
git add -A
git commit -m "revert: rollback to status-based queries"
git push origin main
```

Old queries will continue working indefinitely while status column exists.

## Post-Update Benefits

- **Explicit queries** - No ambiguity about held/disposed stories
- **Trigger-independent** - Works even if sync trigger removed
- **Index-optimized** - Uses partial indexes on three-field columns
- **Future-proof** - Ready for eventual status column removal

## GitHub Actions Testing

**Manual workflow run:**
1. Go to Actions → Story Tree Orchestrator
2. Click "Run workflow"
3. Set `max_cycles: 1` (test run)
4. Monitor logs for query results
5. Verify approved story detected correctly

**Check for errors:**
- No Python SQL syntax errors
- Approved stories found when expected
- No changes to story selection logic (same stories planned)

## When NOT to Proceed

⛔ **Abort if:**
- Database not yet migrated to three-field (handover incomplete)
- Status column already removed (these queries won't work)
- Active workflow runs in progress (wait for completion)
- Unsure about query equivalence (test locally first)
