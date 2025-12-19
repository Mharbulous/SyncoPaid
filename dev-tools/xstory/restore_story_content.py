#!/usr/bin/env python3
"""
Restore missing story and success_criteria content from description field.

This script fixes nodes where the original migration failed to parse the
inline format: "As a X, I want Y, so that Z" (comma-separated on one line).

The original migrate_content_fields.py expected newline-separated format:
    As a X
    I want Y
    So that Z

But many nodes use comma-separated inline format which was not matched.

Usage:
    python dev-tools/xstory/restore_story_content.py           # Run restore
    python dev-tools/xstory/restore_story_content.py --dry-run # Preview only
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / '.claude/data/story-tree.db'

# Pattern for inline comma-separated format (the main format that was missed):
# "As a X, I want Y, so that Z" or "As an X, I want Y, so that Z"
STORY_PATTERN_INLINE = re.compile(
    r'^As an?\s+(.+?),\s*I want\s+(.+?),\s*so that\s+(.+?)(?=\n\n|\n?Acceptance|\Z)',
    re.IGNORECASE | re.DOTALL | re.MULTILINE
)

# Pattern for bold markdown acceptance criteria: **Acceptance Criteria:**
CRITERIA_PATTERN_BOLD = re.compile(
    r'\*\*Acceptance Criteria:\*\*\s*\n((?:- .*(?:\n|$))+)',
    re.IGNORECASE
)

# Pattern for plain acceptance criteria: Acceptance Criteria:
CRITERIA_PATTERN_PLAIN = re.compile(
    r'Acceptance Criteria:\s*\n((?:- .*(?:\n|$))+)',
    re.IGNORECASE
)


def parse_description(description: str) -> tuple[str, str, str]:
    """
    Parse description into (story, success_criteria, remaining_description).

    Returns:
        story: "As a X, I want Y, so that Z" (normalized format)
        success_criteria: The criteria list
        description: Any remaining content
    """
    if not description:
        return ('', '', '')

    story = ''
    success_criteria = ''
    remaining = description

    # Try inline comma-separated format (the missed format)
    story_match = STORY_PATTERN_INLINE.search(description)
    if story_match:
        persona = story_match.group(1).strip()
        want = story_match.group(2).strip()
        benefit = story_match.group(3).strip().rstrip('.')
        story = f"As a {persona}, I want {want}, so that {benefit}."
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


def restore():
    """Restore missing story/success_criteria from description field."""
    print(f"Opening database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get nodes that need restoration:
    # - story IS NULL but description contains "As a"
    # - OR success_criteria IS NULL but description contains "Acceptance Criteria"
    cursor.execute("""
        SELECT id, description, story, success_criteria
        FROM story_nodes
        WHERE (
            (story IS NULL AND description LIKE '%As a %')
            OR (success_criteria IS NULL AND description LIKE '%Acceptance Criteria%')
        )
        AND description IS NOT NULL
        AND LENGTH(description) > 20
        ORDER BY id
    """)
    rows = cursor.fetchall()

    print(f"\nFound {len(rows)} nodes that may need restoration\n")

    restored_story = 0
    restored_criteria = 0
    skipped = 0

    for node_id, description, existing_story, existing_criteria in rows:
        parsed_story, parsed_criteria, remaining = parse_description(description or '')

        # Only update fields that are currently NULL and we found content
        updates = []
        params = []

        if existing_story is None and parsed_story:
            updates.append("story = ?")
            params.append(parsed_story)
            restored_story += 1

        if existing_criteria is None and parsed_criteria:
            updates.append("success_criteria = ?")
            params.append(parsed_criteria)
            restored_criteria += 1

        # Update description to the cleaned remaining content (if we extracted anything)
        if updates and remaining != description:
            updates.append("description = ?")
            params.append(remaining)

        if updates:
            params.append(node_id)
            sql = f"UPDATE story_nodes SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            print(f"  Restored {node_id}: story={'Y' if parsed_story else 'N'}, criteria={'Y' if parsed_criteria else 'N'}")
        else:
            skipped += 1

    conn.commit()

    # Update metadata
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('last_restore', ?)
    """, (datetime.now().isoformat(),))
    conn.commit()

    print(f"\n{'='*50}")
    print("Restoration complete:")
    print(f"  Stories restored: {restored_story}")
    print(f"  Criteria restored: {restored_criteria}")
    print(f"  Skipped (nothing to restore): {skipped}")
    print(f"{'='*50}")

    conn.close()


def dry_run():
    """Preview restoration without making changes."""
    print(f"DRY RUN - Opening database: {DB_PATH}\n")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, story, success_criteria
        FROM story_nodes
        WHERE (
            (story IS NULL AND description LIKE '%As a %')
            OR (success_criteria IS NULL AND description LIKE '%Acceptance Criteria%')
        )
        AND description IS NOT NULL
        AND LENGTH(description) > 20
        ORDER BY id
    """)

    would_restore_story = 0
    would_restore_criteria = 0

    for row in cursor.fetchall():
        node_id, title, description, existing_story, existing_criteria = row
        parsed_story, parsed_criteria, remaining = parse_description(description or '')

        print(f"\n{'='*60}")
        print(f"ID: {node_id}")
        print(f"Title: {title}")
        print(f"Existing story: {'Yes' if existing_story else 'No'}")
        print(f"Existing criteria: {'Yes' if existing_criteria else 'No'}")

        if existing_story is None and parsed_story:
            print(f"\n  WOULD RESTORE STORY:")
            print(f"    {parsed_story[:100]}..." if len(parsed_story) > 100 else f"    {parsed_story}")
            would_restore_story += 1

        if existing_criteria is None and parsed_criteria:
            lines = parsed_criteria.count('\n') + 1
            print(f"\n  WOULD RESTORE CRITERIA: ({lines} items)")
            for line in parsed_criteria.split('\n')[:3]:
                print(f"    {line}")
            if lines > 3:
                print(f"    ... and {lines - 3} more items")
            would_restore_criteria += 1

        if remaining and remaining != description:
            print(f"\n  REMAINING DESCRIPTION: {len(remaining)} chars")

    print(f"\n{'='*60}")
    print("DRY RUN SUMMARY:")
    print(f"  Would restore stories: {would_restore_story}")
    print(f"  Would restore criteria: {would_restore_criteria}")
    print(f"\nRun without --dry-run to apply restoration.")

    conn.close()


if __name__ == '__main__':
    import sys

    if '--dry-run' in sys.argv:
        dry_run()
    else:
        restore()
