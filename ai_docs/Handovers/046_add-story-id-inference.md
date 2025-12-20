# Task: Infer Story ID for Orphan Plans

## Objective
Update `.claude/skills/story-execution/SKILL.md` Step 1.5a to attempt matching orphan plans to stories in the database before archiving them.

## Key Files
- `.claude/skills/story-execution/SKILL.md` - Current implementation at lines 104-164
- `.claude/data/story-tree.db` - SQLite database with `story_nodes` table (columns: id, title, description, notes, stage, etc.)
- `.claude/data/plans/*.md` - 46 plan files, none have Story IDs currently

## Current Behavior (Step 1.5a)
1. Extract Story ID from plan content via regex
2. If no Story ID OR Story ID not in database → archive to `orphan/` folder and skip

## Proposed Enhancement
Before archiving as orphan, attempt to infer the Story ID:

1. Extract plan title/slug from filename (e.g., `004A_ui-automation-foundation.md` → "ui automation foundation")
2. Query `story_nodes` for potential matches using title/description similarity
3. If exactly ONE strong match found → prompt for confirmation (interactive) or auto-assign (CI mode with logging)
4. If multiple candidates → list them and require human decision
5. If no candidates → proceed with orphan archival

## Matching Strategy
```sql
-- Search by title keywords
SELECT id, title, stage FROM story_nodes
WHERE title LIKE '%ui%automation%'
  AND disposition IS NULL
ORDER BY id;
```

Consider fuzzy matching on:
- Plan filename slug
- Plan file's `# Title` (first H1)
- Keywords from plan content

## Edge Cases
- XStory GUI plans (001, 003, 015, 021) should NOT match any SyncoPaid stories - they should still be archived as orphans
- Multiple plans may map to same story (sub-plans like 004A, 004B, 004C)

## CI vs Interactive Mode
- **CI Mode:** If single high-confidence match, auto-assign and log the decision. Otherwise skip.
- **Interactive Mode:** Present candidates and ask user to confirm or reject.

## Output Format
When inferring:
```json
{
  "inferred": true,
  "story_id": "4.1",
  "confidence": "high",
  "match_reason": "title keyword match: 'ui automation'"
}
```
