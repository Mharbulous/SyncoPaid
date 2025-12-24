# Migration Plan: Split Description into Story/Success Criteria/Description

## Overview

Split the current `description` field into three semantic fields:
- **story**: User story format ("As a X, I want Y, so that Z")
- **success_criteria**: Acceptance criteria checklist
- **description**: Additional context (remainder)

Keep `notes` field **unchanged** (operational audit trail).

---

## 1. SQL Schema Changes

### Schema Version: v4.1.0

```sql
-- Migration: v4.0.0 → v4.1.0 (Three-Field Content Split)

-- Step 1: Add new columns
ALTER TABLE story_nodes ADD COLUMN story TEXT;
ALTER TABLE story_nodes ADD COLUMN success_criteria TEXT;

-- Step 2: After migration script runs, update constraints
-- Note: SQLite requires table recreation for NOT NULL changes
-- The 'description' field becomes optional (can be empty string)
```

### Final Schema (story_nodes excerpt)

```sql
CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,

    -- Content fields (v4.1.0 - Three-Field Content Split)
    story TEXT,                    -- "As a X, I want Y, so that Z"
    success_criteria TEXT,         -- Acceptance criteria checklist
    description TEXT DEFAULT '',   -- Additional context (optional)

    -- ... remaining fields unchanged ...
    notes TEXT,                    -- Operational logs (UNCHANGED)
);
```

---

## 2. Python Migration Script

### File: `dev-tools/xstory/migrate_content_fields.py`

```python
#!/usr/bin/env python3
"""
Migration: Split description into story/success_criteria/description
Version: v4.0.0 → v4.1.0

Run: python dev-tools/xstory/migrate_content_fields.py
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / '.claude/data/story-tree.db'

# Regex patterns for parsing description field
STORY_PATTERN = re.compile(
    r'\*\*As a\*\*\s*(.+?)\s*'
    r'\*\*I want\*\*\s*(.+?)\s*'
    r'\*\*So that\*\*\s*(.+?)(?=\n\n|\*\*Acceptance|\Z)',
    re.IGNORECASE | re.DOTALL
)

CRITERIA_PATTERN = re.compile(
    r'\*\*Acceptance Criteria:\*\*\s*\n((?:- \[.\].*(?:\n|$))+)',
    re.IGNORECASE
)


def parse_description(description: str) -> tuple[str, str, str]:
    """
    Parse description into (story, success_criteria, remaining_description).

    Returns:
        story: "As a X, I want Y, so that Z" (plain text, no markdown)
        success_criteria: The criteria list (preserves markdown checkboxes)
        description: Any remaining content
    """
    if not description:
        return ('', '', '')

    story = ''
    success_criteria = ''
    remaining = description

    # Extract user story
    story_match = STORY_PATTERN.search(description)
    if story_match:
        persona = story_match.group(1).strip()
        want = story_match.group(2).strip()
        benefit = story_match.group(3).strip()
        story = f"As a {persona}, I want {want}, so that {benefit}"
        # Remove from remaining
        remaining = remaining[:story_match.start()] + remaining[story_match.end():]

    # Extract acceptance criteria
    criteria_match = CRITERIA_PATTERN.search(remaining)
    if criteria_match:
        success_criteria = criteria_match.group(1).strip()
        # Remove header and criteria from remaining
        full_match_start = remaining.find('**Acceptance Criteria:**')
        if full_match_start != -1:
            remaining = remaining[:full_match_start] + remaining[criteria_match.end():]

    # Clean up remaining description
    remaining = remaining.strip()
    # Remove orphaned empty lines
    remaining = re.sub(r'\n{3,}', '\n\n', remaining)

    return (story, success_criteria, remaining)


def migrate():
    """Run the migration."""
    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Add new columns if they don't exist
    try:
        cursor.execute("ALTER TABLE story_nodes ADD COLUMN story TEXT")
        print("Added 'story' column")
    except sqlite3.OperationalError:
        print("'story' column already exists")

    try:
        cursor.execute("ALTER TABLE story_nodes ADD COLUMN success_criteria TEXT")
        print("Added 'success_criteria' column")
    except sqlite3.OperationalError:
        print("'success_criteria' column already exists")

    conn.commit()

    # Step 2: Migrate existing data
    cursor.execute("SELECT id, description FROM story_nodes")
    rows = cursor.fetchall()

    migrated = 0
    skipped = 0

    for node_id, description in rows:
        story, criteria, remaining = parse_description(description or '')

        if story or criteria:
            cursor.execute("""
                UPDATE story_nodes
                SET story = ?, success_criteria = ?, description = ?
                WHERE id = ?
            """, (story, criteria, remaining, node_id))
            migrated += 1
            print(f"  Migrated: {node_id}")
        else:
            # No structured content found, keep description as-is
            skipped += 1

    conn.commit()

    # Step 3: Update metadata version
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('schema_version', '4.1.0')
    """)
    conn.commit()

    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated} nodes")
    print(f"  Skipped (no structured content): {skipped} nodes")

    conn.close()


def dry_run():
    """Preview migration without making changes."""
    print(f"DRY RUN - Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, description FROM story_nodes WHERE description != '' LIMIT 10")

    for node_id, description in cursor.fetchall():
        story, criteria, remaining = parse_description(description or '')
        print(f"\n{'='*60}")
        print(f"ID: {node_id}")
        print(f"STORY: {story[:100]}..." if len(story) > 100 else f"STORY: {story or '(none)'}")
        print(f"CRITERIA: {len(criteria)} chars" if criteria else "CRITERIA: (none)")
        print(f"REMAINING: {len(remaining)} chars" if remaining else "REMAINING: (none)")

    conn.close()


if __name__ == '__main__':
    import sys
    if '--dry-run' in sys.argv:
        dry_run()
    else:
        migrate()
```

---

## 3. xstory.py DetailView Updates

### Changes Required

#### 3.1 Update StoryNode class (line ~428)

```python
class StoryNode:
    def __init__(self, id: str, title: str, status: str, capacity: Optional[int],
                 description: str = '', depth: int = 0, parent_id: Optional[str] = None,
                 notes: str = '', project_path: str = '', created_at: str = '',
                 updated_at: str = '', last_implemented: str = '',
                 stage: str = '', hold_reason: Optional[str] = None,
                 disposition: Optional[str] = None, descendants_count: int = 0,
                 story: str = '', success_criteria: str = ''):  # NEW FIELDS
        # ... existing fields ...
        self.story = story                        # NEW
        self.success_criteria = success_criteria  # NEW
```

#### 3.2 Update SQL query in _load_nodes() (line ~1527)

```python
query = """
    SELECT
        s.id, s.title,
        COALESCE(s.disposition, s.hold_reason, s.stage) as status,
        s.stage, s.hold_reason, s.disposition,
        s.capacity, s.description,
        s.story, s.success_criteria,  -- NEW FIELDS
        s.notes, s.project_path, s.created_at, s.updated_at,
        ...
"""
```

#### 3.3 Update DetailView._update_detail() (line ~825)

Replace current layout with three sections:

```python
def _update_detail(self):
    # ... header and status row unchanged ...

    # Section 1: Story (user story format)
    if node.story:
        self._add_section_header("Story")
        self._add_text_field(None, node.story)

    # Section 2: Success Criteria (checklist)
    if node.success_criteria:
        self._add_section_header("Success Criteria")
        self._add_text_field(None, node.success_criteria)

    # Section 3: Description (additional context)
    if node.description:
        self._add_section_header("Description")
        self._add_text_field(None, node.description)

    # Section 4: Metadata card (unchanged)
    # Section 5: Notes (unchanged - operational logs)
```

---

## 4. Backward Compatibility

### Reading (safe)
- New code checks `story` field first, falls back to parsing `description`
- Old databases work until migrated

### Writing (requires migration)
- New stories written to separate fields
- Old skill scripts need updates to write to correct fields

### Skill Updates Required

| Skill | File | Change |
|-------|------|--------|
| story-writing | SKILL.md | Write to `story` + `success_criteria` fields |
| story-planning | SKILL.md | Read from new fields |
| story-execution | SKILL.md | Read success_criteria for verification |

---

## 5. Migration Steps

### Pre-Migration
1. [ ] Backup database: `cp .claude/data/story-tree.db .claude/data/story-tree.db.backup`
2. [ ] Run dry-run: `python dev-tools/xstory/migrate_content_fields.py --dry-run`
3. [ ] Review output for parsing accuracy

### Migration
4. [ ] Run migration: `python dev-tools/xstory/migrate_content_fields.py`
5. [ ] Verify with xstory GUI that fields display correctly

### Post-Migration
6. [ ] Update schema.sql reference file
7. [ ] Update skill files to use new fields
8. [ ] Update xstory.py DetailView
9. [ ] Test full workflow (create story → verify display)

---

## 6. Rollback Plan

If migration fails:
```bash
# Restore from backup
cp .claude/data/story-tree.db.backup .claude/data/story-tree.db
```

If partial migration (some rows migrated):
```sql
-- Rollback by restoring description from parsed fields
UPDATE story_nodes
SET description =
    CASE WHEN story IS NOT NULL THEN
        '**As a** ' || story || E'\n\n**Acceptance Criteria:**\n' || success_criteria
    ELSE description END
WHERE story IS NOT NULL;

-- Drop new columns (requires table recreation in SQLite)
```

---

## 7. Field Mapping Summary

| Old | New | Content |
|-----|-----|---------|
| `description` (part 1) | `story` | "As a X, I want Y, so that Z" |
| `description` (part 2) | `success_criteria` | `- [ ] criteria...` checklist |
| `description` (part 3) | `description` | Remaining context |
| `notes` | `notes` | **UNCHANGED** - operational logs |

---

## Open Questions Resolved

1. **Migration strategy for existing `description` data → which new field?**
   - **Answer**: Split into THREE fields via regex parsing. Story format → `story`, criteria → `success_criteria`, remainder → `description`

2. **Keep `notes` field separate or merge into `description`?**
   - **Answer**: Keep SEPARATE. `notes` is operational audit trail with timestamps, `description` is static content context.
