# Sub-Plan C: Skill Updates and Integration Testing

## Overview

Update story-tree skills to write to the new fields and run integration testing.

**Parent Plan**: 015_story-tree-three-field-migration.md
**Depends On**: 015A (migration script), 015B (xstory display)

---

## TDD Tasks

### Task 1: Run migration on actual database

**Pre-requisite**: Backup database first

```bash
cp .claude/data/story-tree.db .claude/data/story-tree.db.backup-v4.0
cd dev-tools/xstory
python migrate_content_fields.py --dry-run
# Review output
python migrate_content_fields.py
```

**Verify**:
```bash
sqlite3 .claude/data/story-tree.db "SELECT id, story, success_criteria FROM story_nodes WHERE story != '' LIMIT 3"
```

---

### Task 2: Update story-writing skill

**File**: `.claude/skills/story-writing/SKILL.md` (or related)

Update the skill to:
1. Write user story to `story` column
2. Write acceptance criteria to `success_criteria` column
3. Write additional context to `description` column

**Verify**: Generate a new story concept, verify fields are populated correctly

---

### Task 3: Update story-planning skill

**File**: `.claude/skills/story-planning/SKILL.md` (or related)

Update the skill to read from new fields when loading story context.

**Verify**: Run story-planning on an existing story, verify it reads from correct fields

---

### Task 4: Update story-execution skill

**File**: `.claude/skills/story-execution/SKILL.md` (or related)

Update to read `success_criteria` for verification checklist during implementation.

**Verify**: Execute a story, verify success criteria are loaded correctly

---

### Task 5: Update schema.sql reference

**File**: `dev-tools/xstory/schema.sql` (or similar)

Update the reference schema to reflect v4.1.0 with new columns.

**Verify**: Schema file matches actual database structure

---

### Task 6: End-to-end integration test

Full workflow test:
1. Create a new story concept (write-story skill)
2. Verify xstory displays three fields correctly
3. Plan the story (story-planning skill)
4. Execute the story (story-execution skill)
5. Verify success criteria are checked

**Verify**: Complete workflow without errors

---

## Verification Checklist

- [ ] Database migrated successfully
- [ ] story-writing skill writes to new fields
- [ ] story-planning skill reads from new fields
- [ ] story-execution skill uses success_criteria
- [ ] schema.sql updated to v4.1.0
- [ ] End-to-end workflow verified
- [ ] Original backup preserved at story-tree.db.backup-v4.0
