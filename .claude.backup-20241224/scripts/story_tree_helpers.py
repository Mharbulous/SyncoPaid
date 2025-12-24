#!/usr/bin/env python3
"""Helper script for story-tree database operations.

Consolidates common database queries to reduce token usage in skills.
"""
import sqlite3
import os
import json
from datetime import date

DB_PATH = '.claude/data/story-tree.db'
GOALS_DIR = '.claude/data/goals'
META_FILE = f'{GOALS_DIR}/synthesis-meta.json'


def get_prerequisites():
    """Return all prerequisite data in one call.

    Compares current DB counts against synthesis-meta.json to determine
    if re-synthesis is needed. Much more efficient than date-based checks.
    """
    result = {
        'db_exists': os.path.exists(DB_PATH),
        'approved_count': 0,
        'rejected_with_notes_count': 0,
        'needs_goals_update': True,
        'needs_non_goals_update': True,
        'last_synthesis': None,
    }

    # Get current counts from database
    if result['db_exists']:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Three-field system: approved stage with no hold/disposition
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE stage = 'approved' AND hold_reason IS NULL AND disposition IS NULL")
        result['approved_count'] = cursor.fetchone()[0]
        # Rejected disposition with notes
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE disposition = 'rejected' AND notes IS NOT NULL AND notes != ''")
        result['rejected_with_notes_count'] = cursor.fetchone()[0]
        conn.close()

    # Compare against last synthesis metadata
    if os.path.exists(META_FILE):
        with open(META_FILE) as f:
            meta = json.load(f)
        result['last_synthesis'] = meta.get('last_synthesis')
        # Only update if counts have changed
        result['needs_goals_update'] = result['approved_count'] != meta.get('approved_count', 0)
        result['needs_non_goals_update'] = result['rejected_with_notes_count'] != meta.get('rejected_with_notes_count', 0)

    print(json.dumps(result, indent=2))
    return result


def update_synthesis_meta():
    """Update synthesis-meta.json after successful synthesis."""
    today = date.today().strftime('%Y-%m-%d')

    # Get current counts
    approved_count = 0
    rejected_count = 0

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE stage = 'approved' AND hold_reason IS NULL AND disposition IS NULL")
        approved_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE disposition = 'rejected' AND notes IS NOT NULL AND notes != ''")
        rejected_count = cursor.fetchone()[0]
        conn.close()

    meta = {
        'last_synthesis': today,
        'approved_count': approved_count,
        'rejected_with_notes_count': rejected_count
    }

    os.makedirs(GOALS_DIR, exist_ok=True)
    with open(META_FILE, 'w') as f:
        json.dump(meta, f, indent=2)
        f.write('\n')

    print(json.dumps({'status': 'updated', **meta}, indent=2))


def get_approved_stories():
    """Output approved stories for goal synthesis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Three-field system: approved stage with no hold/disposition
    cursor.execute('''
        SELECT id, title, description, notes FROM story_nodes
        WHERE stage = 'approved' AND hold_reason IS NULL AND disposition IS NULL
        ORDER BY id
    ''')
    for row in cursor.fetchall():
        print(f'=== {row[0]}: {row[1]} ===')
        print(row[2])
        if row[3]:
            print(f'Notes: {row[3]}')
        print()
    conn.close()


def get_rejected_stories():
    """Output rejected stories with notes for non-goals synthesis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Three-field system: rejected disposition with notes
    cursor.execute('''
        SELECT id, title, description, notes FROM story_nodes
        WHERE disposition = 'rejected' AND notes IS NOT NULL AND notes != ''
        ORDER BY id
    ''')
    for row in cursor.fetchall():
        print(f'=== {row[0]}: {row[1]} ===')
        print(row[2])
        print(f'REJECTION REASON: {row[3]}')
        print()
    conn.close()


if __name__ == '__main__':
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'prereq'
    commands = {
        'prereq': get_prerequisites,
        'approved': get_approved_stories,
        'rejected': get_rejected_stories,
        'update-meta': update_synthesis_meta
    }
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)
