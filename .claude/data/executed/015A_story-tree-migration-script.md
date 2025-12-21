# Sub-Plan A: Migration Script and Schema Changes

## Overview

Create the migration script and apply schema changes to add `story` and `success_criteria` columns.

Parent plan: `015_story-tree-three-field-migration.md`

---

## TDD Tasks

### Task 1: Create migration script with parsing logic

**File**: `dev-tools/xstory/migrate_content_fields.py`

**Test approach**: Unit tests for `parse_description()` function

```python
# Test cases for parse_description()
def test_parse_description_with_full_content():
    desc = """**As a** developer **I want** feature X **So that** benefit Y

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

Additional context here."""
    story, criteria, remaining = parse_description(desc)
    assert "As a developer" in story
    assert "Criterion 1" in criteria
    assert "Additional context" in remaining

def test_parse_description_empty():
    assert parse_description('') == ('', '', '')

def test_parse_description_no_structured_content():
    desc = "Just plain text without structure"
    story, criteria, remaining = parse_description(desc)
    assert story == ''
    assert criteria == ''
    assert remaining == desc
```

**Implementation**: Create the full migration script as specified in the parent plan.

---

### Task 2: Add dry-run capability

**Test approach**: Manual verification

```bash
python dev-tools/xstory/migrate_content_fields.py --dry-run
```

**Expected output**: Shows parsed fields for sample nodes without making changes.

---

### Task 3: Run migration on database

**Pre-requisite**: Backup database first

```bash
cp .claude/data/story-tree.db .claude/data/story-tree.db.backup
python dev-tools/xstory/migrate_content_fields.py
```

**Verification**:
```sql
-- Check columns exist
PRAGMA table_info(story_nodes);

-- Check data migrated
SELECT id, story, success_criteria FROM story_nodes WHERE story IS NOT NULL LIMIT 5;

-- Check schema version
SELECT * FROM metadata WHERE key = 'schema_version';
```

---

## Completion Criteria

- [ ] Migration script created at `dev-tools/xstory/migrate_content_fields.py`
- [ ] Dry-run shows correct parsing of existing descriptions
- [ ] Migration runs successfully
- [ ] Schema version updated to 4.1.0
- [ ] Database backup exists
