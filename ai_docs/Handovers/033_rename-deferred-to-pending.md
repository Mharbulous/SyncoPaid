# Handover: Rename `deferred` Status to `pending`

## Task

Complete the `deferred` → `pending` status rename. User has done find/replace in codebase. You need to:

1. Verify the find/replace was applied correctly
2. Run database migration: `UPDATE story_nodes SET status='pending' WHERE status='deferred'`
3. Update the story-vetting skill to use `pending` for HUMAN_REVIEW cases in CI

## Context

**Goal**: Enable story-vetting skill to run in CI by having it set conflicting stories to `pending` status instead of blocking for interactive input.

**Integration point**: Story-vetting should run as step 3 in the orchestrator loop:
```
drain-pipeline loop:
  1. plan-stories (drain approved)
  2. write-stories (fill capacity)
  3. vet-stories (resolve conflicts)  ← uses pending for HUMAN_REVIEW
  4. Check if idle
```

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/story-vetting/SKILL.md` | Skill definition — needs CI mode logic |
| `ai_docs/Orchestrator/2025-12-16-Dev-Workflow.md` | Orchestrator documentation |
| `.github/workflows/story-tree-orchestrator.yml` | Workflow to eventually integrate vetting |
| `dev-tools/xstory/xstory.py` | Status transitions — verify `pending` works |
| `.claude/skills/story-tree/references/schema.sql` | Schema reference |

## Database State

Before migration:
- 1 story with `deferred` status: `1.4.6: Activity Timeline View`

Migration command:
```python
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute("UPDATE story_nodes SET status='pending' WHERE status='deferred'")
conn.commit()
conn.close()
```

## Files Changed by Find/Replace

Expect `deferred` → `pending` in:
- `dev-tools/xstory/xstory.py` (color, transitions)
- `dev-tools/xstory/migrate_status_schema.py`
- `.claude/skills/story-vetting/SKILL.md` (BLOCK_STATUSES)
- `.claude/skills/story-tree/SKILL.md`
- `.claude/skills/story-tree/references/schema.sql`
- `.claude/skills/story-tree/scripts/tree-view.py`
- `.claude/skills/story-tree/scripts/migrate_v1_to_v2.py`

## Ignore (Archived)

- `archived/story-tree-explorer/*.py` — old code, don't prioritize

## Next Steps After Migration

1. Modify story-vetting skill to handle CI mode:
   - For HUMAN_REVIEW cases: set status to `pending` instead of prompting
   - Add conflict info to `notes` field
   - Return summary of actions taken

2. Update orchestrator workflow to call vet-stories after write-stories

## Decision Record

- Chose `pending` over `flagged` because it fits the existing status naming pattern (states of being: approved, rejected, planned) rather than actions taken
- `pending` implies "waiting for human review" which matches the use case
