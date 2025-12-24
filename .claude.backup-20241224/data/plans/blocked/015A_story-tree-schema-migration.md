# Sub-Plan A: Schema Migration and Migration Script

## Overview

Add the new `story` and `success_criteria` columns to the story-tree database and create the migration script to parse existing description content.

**Parent Plan**: 015_story-tree-three-field-migration.md
**Schema Version**: v4.0.0 → v4.1.0

---

## TDD Tasks

### Task 1: Write tests for parse_description function

**Test file**: `dev-tools/xstory/test_migrate_content_fields.py`

```python
import pytest
from migrate_content_fields import parse_description

def test_parse_empty_description():
    """Empty description returns empty tuple."""
    assert parse_description('') == ('', '', '')
    assert parse_description(None) == ('', '', '')

def test_parse_story_format():
    """Extracts user story from markdown format."""
    desc = """**As a** developer
**I want** to track my work
**So that** I can bill accurately"""
    story, criteria, remaining = parse_description(desc)
    assert story == "As a developer, I want to track my work, so that I can bill accurately"
    assert criteria == ''
    assert remaining == ''

def test_parse_acceptance_criteria():
    """Extracts acceptance criteria checklist."""
    desc = """Some context.

**Acceptance Criteria:**
- [ ] First criterion
- [ ] Second criterion
- [x] Completed criterion

More context."""
    story, criteria, remaining = parse_description(desc)
    assert "- [ ] First criterion" in criteria
    assert "- [x] Completed criterion" in criteria
    assert "More context" in remaining

def test_parse_full_description():
    """Parses complete description with all sections."""
    desc = """**As a** user
**I want** feature X
**So that** I benefit

**Acceptance Criteria:**
- [ ] Must do A
- [ ] Must do B

Additional notes here."""
    story, criteria, remaining = parse_description(desc)
    assert "As a user" in story
    assert "- [ ] Must do A" in criteria
    assert "Additional notes" in remaining
```

**Verify**: `cd dev-tools/xstory && python -m pytest test_migrate_content_fields.py -v`

---

### Task 2: Implement parse_description function

**File**: `dev-tools/xstory/migrate_content_fields.py`

Create the migration script with:
1. Regex patterns for story format extraction
2. Regex patterns for acceptance criteria extraction
3. `parse_description()` function that splits content into three fields
4. Clean handling of edge cases (empty, partial, missing sections)

**Verify**: Tests from Task 1 pass

---

### Task 3: Write tests for schema column addition

```python
def test_add_columns_idempotent(tmp_path):
    """Adding columns twice doesn't error."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE story_nodes (id TEXT, description TEXT)")

    # First addition
    add_schema_columns(conn)

    # Verify columns exist
    cursor = conn.execute("PRAGMA table_info(story_nodes)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'story' in columns
    assert 'success_criteria' in columns

    # Second addition should not error
    add_schema_columns(conn)  # No exception
```

**Verify**: Tests pass

---

### Task 4: Implement column addition with idempotency

Add `add_schema_columns()` function to migration script that:
1. Uses ALTER TABLE to add `story TEXT` column
2. Uses ALTER TABLE to add `success_criteria TEXT` column
3. Catches OperationalError for existing columns (idempotent)

**Verify**: Task 3 tests pass

---

### Task 5: Write migration dry-run and execute functions

Add:
1. `dry_run()` - Preview migration without changes, show sample parsing
2. `migrate()` - Execute full migration with progress reporting
3. CLI entry point with `--dry-run` flag

**Verify**:
```bash
cd dev-tools/xstory
python migrate_content_fields.py --dry-run
# Should show sample parsed content without modifying database
```

---

## Verification Checklist

- [ ] All tests in `test_migrate_content_fields.py` pass
- [ ] `--dry-run` shows correct parsing for existing story_nodes
- [ ] Migration script is importable and functions are testable
- [ ] No changes to actual database in this sub-plan (testing only)
