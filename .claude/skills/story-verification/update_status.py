#!/usr/bin/env python3
"""
Update story status based on verification results.

Usage:
  python update_status.py <story_id> <new_status> ["<verification_notes>"]
  python update_status.py <story_id> mark-criteria <criterion_indices>

Actions:
  - Update story status with verification notes
  - Mark specific criteria as checked in description
"""
import json
import re
import sqlite3
import sys


VALID_STATUSES = {
    'infeasible', 'rejected', 'wishlist',
    'concept', 'broken', 'blocked', 'refine',
    'pending', 'approved', 'planned', 'queued', 'paused',
    'active',
    'reviewing', 'implemented',
    'ready', 'polish', 'released',
    'legacy', 'deprecated', 'archived'
}


def update_status(story_id: str, new_status: str, notes: str = None) -> dict:
    """Update story status and optionally add verification notes."""
    if new_status not in VALID_STATUSES:
        return {"error": f"Invalid status: {new_status}", "valid_statuses": list(VALID_STATUSES)}

    conn = sqlite3.connect('.claude/data/story-tree.db')

    # Get current story
    cursor = conn.execute('SELECT status, notes FROM story_nodes WHERE id = ?', (story_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": f"Story {story_id} not found"}

    old_status = row[0]
    existing_notes = row[1] or ''

    # Build new notes
    if notes:
        new_notes = existing_notes + ('\n' if existing_notes else '') + f"[Verification] {notes}"
    else:
        new_notes = existing_notes

    # Update
    conn.execute('''
        UPDATE story_nodes
        SET status = ?, notes = ?, updated_at = datetime('now')
        WHERE id = ?
    ''', (new_status, new_notes, story_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "story_id": story_id,
        "old_status": old_status,
        "new_status": new_status,
        "notes_added": notes is not None
    }


def mark_criteria_checked(story_id: str, indices: list[int]) -> dict:
    """Mark specific acceptance criteria as checked in the description."""
    conn = sqlite3.connect('.claude/data/story-tree.db')

    cursor = conn.execute('SELECT description FROM story_nodes WHERE id = ?', (story_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": f"Story {story_id} not found"}

    description = row[0]

    # Find all criteria with their positions
    pattern = r'-\s*\[([ xX])\]\s*(.+?)(?=\n-\s*\[|\n\n|\n\*\*|$)'
    matches = list(re.finditer(pattern, description, re.DOTALL))

    if not matches:
        conn.close()
        return {"error": "No acceptance criteria found in description"}

    # Track which criteria were updated
    updated = []
    new_description = description

    # Process in reverse order to preserve positions
    for idx in sorted(indices, reverse=True):
        if 1 <= idx <= len(matches):
            match = matches[idx - 1]
            checkbox_char = match.group(1)

            if checkbox_char == ' ':
                # Replace unchecked with checked
                start, end = match.span(1)
                new_description = new_description[:start] + 'x' + new_description[end:]
                updated.append(idx)

    if updated:
        conn.execute('''
            UPDATE story_nodes
            SET description = ?, updated_at = datetime('now')
            WHERE id = ?
        ''', (new_description, story_id))
        conn.commit()

    conn.close()

    return {
        "success": True,
        "story_id": story_id,
        "criteria_marked": sorted(updated),
        "total_criteria": len(matches)
    }


def get_verification_summary(story_id: str) -> dict:
    """Get current verification status of a story."""
    conn = sqlite3.connect('.claude/data/story-tree.db')
    conn.row_factory = sqlite3.Row

    story = conn.execute('''
        SELECT id, title, description, status, notes
        FROM story_nodes WHERE id = ?
    ''', (story_id,)).fetchone()

    conn.close()

    if not story:
        return {"error": f"Story {story_id} not found"}

    story_dict = dict(story)
    description = story_dict['description']

    # Count criteria
    pattern = r'-\s*\[([ xX])\]'
    matches = re.findall(pattern, description)

    total = len(matches)
    checked = sum(1 for m in matches if m.lower() == 'x')
    unchecked = total - checked

    return {
        "story_id": story_id,
        "title": story_dict['title'],
        "status": story_dict['status'],
        "criteria_total": total,
        "criteria_checked": checked,
        "criteria_unchecked": unchecked,
        "verification_complete": unchecked == 0 and total > 0
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python update_status.py <story_id> <new_status> [notes]")
        print("  python update_status.py <story_id> mark-criteria 1,2,3")
        print("  python update_status.py <story_id> summary")
        sys.exit(1)

    story_id = sys.argv[1]
    action = sys.argv[2]

    if action == 'summary':
        result = get_verification_summary(story_id)

    elif action == 'mark-criteria':
        if len(sys.argv) < 4:
            print("Error: Specify criterion indices (e.g., 1,2,3)")
            sys.exit(1)
        indices = [int(i.strip()) for i in sys.argv[3].split(',')]
        result = mark_criteria_checked(story_id, indices)

    elif action in VALID_STATUSES:
        notes = sys.argv[3] if len(sys.argv) > 3 else None
        result = update_status(story_id, action, notes)

    else:
        print(f"Error: Unknown action '{action}'")
        print(f"Valid statuses: {', '.join(sorted(VALID_STATUSES))}")
        sys.exit(1)

    print(json.dumps(result, indent=2))
