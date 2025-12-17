#!/usr/bin/env python3
"""
Parse acceptance criteria from story description.

Usage: python parse_criteria.py <story_id>

Output: JSON with story info and parsed criteria
"""
import sqlite3
import json
import re
import sys


def parse_acceptance_criteria(description: str) -> list[dict]:
    """Extract acceptance criteria from story description."""
    criteria = []

    # Match checkbox format: - [ ] or - [x] or - [X]
    pattern = r'-\s*\[([ xX])\]\s*(.+?)(?=\n-\s*\[|\n\n|\n\*\*|$)'

    matches = re.findall(pattern, description, re.DOTALL)

    for idx, (checkbox, text) in enumerate(matches, 1):
        criteria.append({
            "index": idx,
            "text": text.strip(),
            "checked": checkbox.lower() == 'x'
        })

    return criteria


def get_story_criteria(story_id: str) -> dict:
    """Get story and parse its acceptance criteria."""
    conn = sqlite3.connect('.claude/data/story-tree.db')
    conn.row_factory = sqlite3.Row

    story = conn.execute('''
        SELECT id, title, description,
               COALESCE(disposition, hold_reason, stage) AS status,
               project_path
        FROM story_nodes
        WHERE id = ?
    ''', (story_id,)).fetchone()

    conn.close()

    if not story:
        return {"error": f"Story {story_id} not found"}

    story_dict = dict(story)
    criteria = parse_acceptance_criteria(story_dict['description'])

    return {
        "story_id": story_dict['id'],
        "title": story_dict['title'],
        "status": story_dict['status'],
        "project_path": story_dict['project_path'],
        "criteria": criteria,
        "criteria_count": len(criteria),
        "unchecked_count": sum(1 for c in criteria if not c['checked'])
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_criteria.py <story_id>")
        sys.exit(1)

    story_id = sys.argv[1]
    result = get_story_criteria(story_id)
    print(json.dumps(result, indent=2))
