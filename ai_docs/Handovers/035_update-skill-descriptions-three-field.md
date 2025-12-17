# Handover: Update Skill Descriptions for Three-Field System

## Task

Update YAML frontmatter descriptions in skill files to use three-field terminology (`stage`/`hold_reason`/`disposition`) instead of legacy `status` field.

## Context

**Migration Complete:** Commit f45c6df migrated story-tree from 22-status system to orthogonal three-field model:
- `stage` (11 values): workflow position (concept → approved → planned → ... → released)
- `hold_reason` (5 + NULL): why work stopped (pending, blocked, paused, broken, refine)
- `disposition` (6 + NULL): terminal states (rejected, wishlist, archived, etc.)
- `human_review` (boolean): needs attention flag

**What's Done:**
- Database migrated (80 stories, 0 issues verified)
- Python scripts updated
- SQL queries in skill bodies updated
- Backward-compatible `status` column maintained via trigger

**What's Left:**
- YAML frontmatter descriptions still reference old `status=` syntax
- Need consistency for skill invocation clarity

## Key Files to Modify

| File | Lines | Change Required |
|------|-------|-----------------|
| `.claude\skills\story-writing\SKILL.md` | 3, 16 | `status='refine'` → `hold_reason='refine'` |
| `.claude\skills\story-vetting\SKILL.md` | 214-216 | Update action descriptions from `status=` to three-field |

## Red Herrings (Do NOT Touch)

- **Python scripts** - Already updated in f45c6df
- **SQL queries in skill bodies** - Already converted
- **Database schema** - Migration complete, verified clean
- **`status` column** - Intentionally kept for backward compatibility

## Reference Files

| File | Purpose |
|------|---------|
| `.claude\skills\story-tree\SKILL.md` | Shows correct three-field usage (updated in f45c6df) |
| `.claude\skills\story-tree\references\schema.sql` | Lines 12-48: Three-field system definition |
| `.claude\data\plans\meta-workflow-three-field.json` | Design rationale and field semantics |
| `.claude\skills\story-tree\scripts\migrate_to_three_field.py` | Lines 30-56: Status → three-field mappings |

## Implementation

### 1. story-writing SKILL.md

**Line 3 (description):**
```diff
-description: ... FIRST refines any existing stories with status='refine' before ...
+description: ... FIRST refines any existing stories with hold_reason='refine' before ...
```

**Line 16 (priority order):**
```diff
-1. **FIRST:** Refine any stories with `status='refine'`
+1. **FIRST:** Refine any stories with `hold_reason='refine'`
```

### 2. story-vetting SKILL.md

**Lines 214-216 (action descriptions):**
```diff
-| REJECT_CONCEPT | ... | Set status=rejected with note |
-| BLOCK_CONCEPT | ... | Set status=blocked with note |
-| DEFER_PENDING | ... | Set status=pending (CI mode) |
+| REJECT_CONCEPT | ... | Set disposition=rejected with note |
+| BLOCK_CONCEPT | ... | Set hold_reason=blocked with note |
+| DEFER_PENDING | ... | Set hold_reason=pending (CI mode) |
```

## Verification

After changes:
```bash
# Confirm no more status= references in descriptions
python -c "import re; paths = ['.claude/skills/story-writing/SKILL.md', '.claude/skills/story-vetting/SKILL.md']; [print(f'{p}: {len(re.findall(r\"status\\s*=\", open(p, encoding=\"utf-8\").read()))} matches') for p in paths]"
# Expected: Both should show 0 matches
```

## Why This Matters

- Skill descriptions appear in Claude Code UI when browsing skills
- Outdated terminology confuses users about current workflow model
- Consistency between documentation and implementation prevents bugs

## Design Resources

**Three-field system explained:**
- Stage = where in pipeline (linear progression)
- Hold = why stopped (orthogonal to stage, preserves resume point)
- Disposition = terminal exit (story left pipeline, stage preserved)

**Key insight:** Unlike old status system, stage is PRESERVED when story held/disposed, so you know exactly where to resume work.

See schema.sql lines 139-174 for complete reference documentation.
