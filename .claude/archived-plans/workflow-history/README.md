# Archived Workflow Documentation

These files document historical workflow designs that have been superseded by the **three-field system** (stage + hold_reason + disposition).

## Current System

The current workflow uses the three-field system documented in:
- `.claude/skills/story-tree/SKILL.md`
- `.claude/skills/story-tree/references/schema.sql`
- `.claude/data/plans/meta-workflow-three-field.json`

## Archived Files

| File | Description |
|------|-------------|
| `meta-workflow-one-field.json` | Original 22-status single-field design |
| `meta-workflow-two-field.json` | Proposed two-field alternative (status + human_review) |
| `meta-workflow.json` | Original workflow implementation notes |
| `meta-workflow.md` | Original workflow documentation |
| `2025-12-16-*.md` | Token optimization plans (reference old status column) |

## Why Archived

These documents reference the deprecated `status` column which was removed in favor of the three-field system. They are preserved for historical reference but should not be used as current documentation.

**Migration completed:** December 2025
