# Sub-Plan A: Migration Script Creation and Execution

## Overview

Create the Python migration script to add new columns and parse existing description data into the three new semantic fields.

Parent plan: `015_story-tree-three-field-migration.md`

---

## TDD Tasks

### Task 1: Create migration script with parsing logic

**File**: `dev-tools/xstory/migrate_content_fields.py`

**Test (write first)**:
```python
# Test parsing logic before implementing
def test_parse_description_with_full_content():
    description = """**As a** developer
**I want** to split fields
**So that** content is semantic

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

Additional context here."""

    story, criteria, remaining = parse_description(description)
    assert "As a developer" in story
    assert "- [ ] Criterion 1" in criteria
    assert "Additional context" in remaining
```

**Implementation**:
- Create script with `parse_description()` function
- Handle regex patterns for story format and acceptance criteria
- Handle edge cases (empty description, missing sections)

**Verification**:
```bash
python -c "from dev-tools.xstory.migrate_content_fields import parse_description; print(parse_description('test'))"
```

---

### Task 2: Add dry-run functionality

**Test**:
```bash
python dev-tools/xstory/migrate_content_fields.py --dry-run
# Should output parsing preview without modifying database
```

**Implementation**:
- Add `--dry-run` CLI argument handling
- Print parsed results for first 10 rows
- Do NOT commit any database changes

---

### Task 3: Add column migration logic

**Test**:
```sql
-- After running migration, columns should exist
SELECT story, success_criteria FROM story_nodes LIMIT 1;
```

**Implementation**:
- Add `ALTER TABLE` statements with error handling for existing columns
- Update schema version to 4.1.0 in metadata table

---

### Task 4: Execute migration with data parsing

**Pre-condition**: Backup database first

**Test**:
```sql
-- Verify migration worked
SELECT id, story, success_criteria, description
FROM story_nodes
WHERE story IS NOT NULL AND story != ''
LIMIT 5;
```

**Implementation**:
- Parse each row's description field
- Update rows with extracted story, success_criteria, remaining description
- Report migration statistics

---

## Completion Criteria

- [ ] `parse_description()` function correctly splits content
- [ ] Dry-run mode previews without changes
- [ ] Migration adds columns if missing
- [ ] Migration parses and updates existing data
- [ ] Schema version updated to 4.1.0
