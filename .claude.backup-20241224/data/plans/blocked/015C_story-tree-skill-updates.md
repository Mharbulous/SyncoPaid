# Sub-Plan C: Skill File Updates

## Overview

Update skill SKILL.md files to write to and read from the new `story` and `success_criteria` fields.

Parent plan: `015_story-tree-three-field-migration.md`
Depends on: `015B_story-tree-xstory-updates.md` (xstory must display new fields)

---

## TDD Tasks

### Task 1: Update story-writing skill

**File**: `.claude/skills/story-writing/SKILL.md`

**Test approach**: Create a test story and verify field separation

**Changes required**:
- Update INSERT/UPDATE statements to populate `story` field with user story format
- Update to populate `success_criteria` field with acceptance criteria checklist
- Update to populate `description` field with additional context only

**Verification**:
```sql
-- After creating a new story, verify fields
SELECT id, story, success_criteria, description
FROM story_nodes WHERE id = '<new_story_id>';
-- story should contain "As a..."
-- success_criteria should contain "- [ ]..."
-- description should contain only context (no story format)
```

---

### Task 2: Update story-planning skill

**File**: `.claude/skills/story-planning/SKILL.md`

**Test approach**: Verify planning reads from correct fields

**Changes required**:
- Read `story` field for user story context
- Read `success_criteria` field for acceptance criteria
- Read `description` field for additional context

---

### Task 3: Update story-execution skill

**File**: `.claude/skills/story-execution/SKILL.md`

**Test approach**: Verify execution uses success_criteria for verification

**Changes required**:
- Read `success_criteria` field to verify implementation completeness
- Update any references that parsed criteria from description

---

### Task 4: Update schema.sql reference

**File**: `.claude/data/schema.sql` (or equivalent reference file)

**Changes required**:
- Add `story TEXT` column definition
- Add `success_criteria TEXT` column definition
- Update schema version comment to v4.1.0

---

## Completion Criteria

- [ ] story-writing skill writes to new fields
- [ ] story-planning skill reads from new fields
- [ ] story-execution skill uses success_criteria for verification
- [ ] Schema reference file updated
- [ ] Full workflow tested: create story → plan → execute → verify display
