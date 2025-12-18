#!/usr/bin/env python3
"""
Update story stage and hold_reason based on verification results.

Usage:
  python update_status.py <story_id> <new_stage> ["<verification_notes>"]
  python update_status.py <story_id> mark-criteria <criterion_indices>

Actions:
  - Update story stage with verification notes
  - Mark specific criteria as checked in description
"""
import json
import os
import re
import sqlite3
import sys

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import DB_PATH

# Valid stages for the three-field system
VALID_STAGES = {
    'concept', 'approved', 'planned', 'active',
    'reviewing', 'verifying', 'implemented', 'ready', 'polish', 'released'
}


def update_status(story_id: str, new_stage: str, notes: str = None, hold: bool = False) -> dict:
    """Update story stage and optionally add verification notes.

    Args:
        story_id: The story ID to update
        new_stage: The new stage value (e.g., 'implemented', 'verifying')
        notes: Optional verification notes to append
        hold: If True, set hold_reason='pending' and human_review=1 (for failures/untestable)
    """
    if new_stage not in VALID_STAGES:
        return {"error": f"Invalid stage: {new_stage}", "valid_stages": list(VALID_STAGES)}

    conn = sqlite3.connect(DB_PATH)

    # Get current story
    cursor = conn.execute('SELECT stage, hold_reason, notes FROM story_nodes WHERE id = ?', (story_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": f"Story {story_id} not found"}

    old_stage = row[0]
    old_hold = row[1]
    existing_notes = row[2] or ''

    # Build new notes
    if notes:
        new_notes = existing_notes + ('\n' if existing_notes else '') + f"[Verification] {notes}"
    else:
        new_notes = existing_notes

    # Update based on hold flag
    if hold:
        # Keep stage, set hold_reason for human review
        conn.execute('''
            UPDATE story_nodes
            SET hold_reason = 'pending', human_review = 1,
                notes = ?, updated_at = datetime('now')
            WHERE id = ?
        ''', (new_notes, story_id))
    else:
        # Update stage, clear any hold
        conn.execute('''
            UPDATE story_nodes
            SET stage = ?, hold_reason = NULL, human_review = 0,
                notes = ?, updated_at = datetime('now')
            WHERE id = ?
        ''', (new_stage, new_notes, story_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "story_id": story_id,
        "old_stage": old_stage,
        "new_stage": new_stage if not hold else old_stage,
        "hold_set": hold,
        "notes_added": notes is not None
    }


def mark_criteria_checked(story_id: str, indices: list[int]) -> dict:
    """Mark specific acceptance criteria as checked in the description."""
    conn = sqlite3.connect(DB_PATH)

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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    story = conn.execute('''
        SELECT id, title, description, stage, hold_reason, disposition, human_review, notes
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
        "stage": story_dict['stage'],
        "hold_reason": story_dict['hold_reason'],
        "human_review": bool(story_dict['human_review']),
        "criteria_total": total,
        "criteria_checked": checked,
        "criteria_unchecked": unchecked,
        "verification_complete": unchecked == 0 and total > 0
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python update_status.py <story_id> <new_stage> [notes]")
        print("  python update_status.py <story_id> <new_stage> --hold [notes]")
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

    elif action in VALID_STAGES:
        # Check for --hold flag
        hold = '--hold' in sys.argv
        # Get notes (skip --hold if present)
        notes_args = [a for a in sys.argv[3:] if a != '--hold']
        notes = notes_args[0] if notes_args else None
        result = update_status(story_id, action, notes, hold=hold)

    else:
        print(f"Error: Unknown action '{action}'")
        print(f"Valid stages: {', '.join(sorted(VALID_STAGES))}")
        sys.exit(1)

    print(json.dumps(result, indent=2))
