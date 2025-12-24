#!/usr/bin/env python3
"""
Migration: Split description into story/success_criteria/description
Version: v4.0.0 → v4.1.0

Splits the monolithic 'description' field into three semantic fields:
- story: User story format ("As a X, I want Y, so that Z")
- success_criteria: Acceptance criteria checklist
- description: Additional context (remainder)

The 'notes' field is left UNCHANGED (operational audit trail).

Usage:
    python dev-tools/xstory/migrate_content_fields.py           # Run migration
    python dev-tools/xstory/migrate_content_fields.py --dry-run # Preview only
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / '.claude/data/story-tree.db'

# Regex patterns for parsing description field
# Format 1 (bold): **As a** X **I want** Y **So that** Z
STORY_PATTERN_BOLD = re.compile(
    r'\*\*As a\*\*\s*(.+?)\s*'
    r'\*\*I want\*\*\s*(.+?)\s*'
    r'\*\*So that\*\*\s*(.+?)(?=\n\n|\*\*Acceptance|\Z)',
    re.IGNORECASE | re.DOTALL
)

# Format 2 (plain): As a X\nI want Y\nSo that Z
STORY_PATTERN_PLAIN = re.compile(
    r'^As a\s+(.+?)\n'
    r'I want\s+(.+?)\n'
    r'So that\s+(.+?)(?=\n\n|Acceptance|\Z)',
    re.IGNORECASE | re.DOTALL | re.MULTILINE
)

# Matches: **Acceptance Criteria:** OR Acceptance Criteria: followed by checklist/list items
CRITERIA_PATTERN_BOLD = re.compile(
    r'\*\*Acceptance Criteria:\*\*\s*\n((?:- \[.\].*(?:\n|$))+)',
    re.IGNORECASE
)

CRITERIA_PATTERN_PLAIN = re.compile(
    r'Acceptance Criteria:\s*\n((?:- .*(?:\n|$))+)',
    re.IGNORECASE
)


def parse_description(description: str) -> tuple[str, str, str]:
    """
    Parse description into (story, success_criteria, remaining_description).

    Handles two formats:
    - Bold: **As a** X **I want** Y **So that** Z
    - Plain: As a X\\nI want Y\\nSo that Z

    Returns:
        story: "As a X, I want Y, so that Z" (plain text, no markdown bold)
        success_criteria: The criteria list (preserves markdown checkboxes)
        description: Any remaining content not matched by above patterns
    """
    if not description:
        return ('', '', '')

    story = ''
    success_criteria = ''
    remaining = description

    # Try bold format first, then plain format
    story_match = STORY_PATTERN_BOLD.search(description)
    if not story_match:
        story_match = STORY_PATTERN_PLAIN.search(description)

    if story_match:
        persona = story_match.group(1).strip()
        want = story_match.group(2).strip()
        benefit = story_match.group(3).strip()
        story = f"As a {persona}, I want {want}, so that {benefit}"
        # Remove matched portion from remaining
        remaining = remaining[:story_match.start()] + remaining[story_match.end():]

    # Try bold criteria format first, then plain format
    criteria_match = CRITERIA_PATTERN_BOLD.search(remaining)
    header_text = '**Acceptance Criteria:**'
    if not criteria_match:
        criteria_match = CRITERIA_PATTERN_PLAIN.search(remaining)
        header_text = 'Acceptance Criteria:'

    if criteria_match:
        success_criteria = criteria_match.group(1).strip()
        # Find and remove the full header + criteria block
        full_match_start = remaining.find(header_text)
        if full_match_start != -1:
            remaining = remaining[:full_match_start] + remaining[criteria_match.end():]

    # Clean up remaining description
    remaining = remaining.strip()
    # Collapse excessive newlines
    remaining = re.sub(r'\n{3,}', '\n\n', remaining)

    return (story, success_criteria, remaining)


def migrate():
    """Run the migration to split description into three fields."""
    print(f"Opening database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Add new columns if they don't exist
    print("\nStep 1: Adding new columns...")
    try:
        cursor.execute("ALTER TABLE story_nodes ADD COLUMN story TEXT")
        print("  Added 'story' column")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("  'story' column already exists")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE story_nodes ADD COLUMN success_criteria TEXT")
        print("  Added 'success_criteria' column")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("  'success_criteria' column already exists")
        else:
            raise

    conn.commit()

    # Step 2: Migrate existing data
    print("\nStep 2: Migrating existing descriptions...")
    cursor.execute("SELECT id, description FROM story_nodes")
    rows = cursor.fetchall()

    migrated = 0
    skipped = 0
    errors = 0

    for node_id, description in rows:
        try:
            story, criteria, remaining = parse_description(description or '')

            if story or criteria:
                cursor.execute("""
                    UPDATE story_nodes
                    SET story = ?, success_criteria = ?, description = ?
                    WHERE id = ?
                """, (story or None, criteria or None, remaining, node_id))
                migrated += 1
                print(f"  Migrated: {node_id}")
            else:
                # No structured content found, keep description as-is
                skipped += 1
        except Exception as e:
            print(f"  ERROR migrating {node_id}: {e}")
            errors += 1

    conn.commit()

    # Step 3: Update metadata version
    print("\nStep 3: Updating schema version...")
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('schema_version', '4.1.0')
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('last_migration', ?)
    """, (datetime.now().isoformat(),))
    conn.commit()

    print(f"\n{'='*50}")
    print("Migration complete:")
    print(f"  Migrated: {migrated} nodes")
    print(f"  Skipped (no structured content): {skipped} nodes")
    print(f"  Errors: {errors} nodes")
    print(f"{'='*50}")

    conn.close()


def dry_run():
    """Preview migration without making changes."""
    print(f"DRY RUN - Opening database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, description
        FROM story_nodes
        WHERE description != ''
        ORDER BY length(description) DESC
        LIMIT 10
    """)

    would_migrate = 0
    would_skip = 0

    for node_id, description in cursor.fetchall():
        story, criteria, remaining = parse_description(description or '')

        print(f"\n{'='*60}")
        print(f"ID: {node_id}")

        if story:
            preview = story[:80] + '...' if len(story) > 80 else story
            print(f"STORY: {preview}")
        else:
            print("STORY: (none found)")

        if criteria:
            lines = criteria.count('\n') + 1
            print(f"CRITERIA: {lines} items ({len(criteria)} chars)")
        else:
            print("CRITERIA: (none found)")

        if remaining:
            print(f"REMAINING: {len(remaining)} chars")
        else:
            print("REMAINING: (empty)")

        if story or criteria:
            would_migrate += 1
        else:
            would_skip += 1

    # Count totals
    cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE description != ''")
    total = cursor.fetchone()[0]

    print(f"\n{'='*60}")
    print(f"SUMMARY (showing first 10 of {total} nodes with descriptions)")
    print(f"  Would migrate: {would_migrate} (in sample)")
    print(f"  Would skip: {would_skip} (in sample)")
    print(f"\nRun without --dry-run to apply migration.")

    conn.close()


def verify():
    """Verify migration results."""
    print(f"Verifying migration: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(story_nodes)")
    columns = [row[1] for row in cursor.fetchall()]

    has_story = 'story' in columns
    has_criteria = 'success_criteria' in columns

    print(f"\nColumn check:")
    print(f"  'story' column: {'EXISTS' if has_story else 'MISSING'}")
    print(f"  'success_criteria' column: {'EXISTS' if has_criteria else 'MISSING'}")

    if has_story and has_criteria:
        # Count populated fields
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE story IS NOT NULL")
        with_story = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE success_criteria IS NOT NULL")
        with_criteria = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM story_nodes")
        total = cursor.fetchone()[0]

        print(f"\nData population:")
        print(f"  Total nodes: {total}")
        print(f"  With story: {with_story}")
        print(f"  With success_criteria: {with_criteria}")

        # Show sample
        cursor.execute("""
            SELECT id, story, success_criteria
            FROM story_nodes
            WHERE story IS NOT NULL
            LIMIT 3
        """)

        print(f"\nSample migrated nodes:")
        for row in cursor.fetchall():
            node_id, story, criteria = row
            print(f"  {node_id}: story={len(story or '')} chars, criteria={len(criteria or '')} chars")

    conn.close()


if __name__ == '__main__':
    import sys

    if '--dry-run' in sys.argv:
        dry_run()
    elif '--verify' in sys.argv:
        verify()
    else:
        migrate()
