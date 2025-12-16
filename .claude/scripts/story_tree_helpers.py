#!/usr/bin/env python3
"""Helper script for story-tree database operations.

Consolidates common database queries to reduce token usage in skills.
"""
import sqlite3
import os
import json
from datetime import date

DB_PATH = '.claude/data/story-tree.db'
XSTORY_DIR = 'ai_docs/Xstory'


def get_prerequisites():
    """Return all prerequisite data in one call."""
    today = date.today().strftime('%Y-%m-%d')

    result = {
        'today': today,
        'db_exists': os.path.exists(DB_PATH),
        'approved_count': 0,
        'rejected_with_notes_count': 0,
        'vision_exists': os.path.exists(f'{XSTORY_DIR}/{today}-user-vision.md'),
        'anti_vision_exists': os.path.exists(f'{XSTORY_DIR}/{today}-user-anti-vision.md'),
    }

    if result['db_exists']:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'approved'")
        result['approved_count'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'rejected' AND notes IS NOT NULL AND notes != ''")
        result['rejected_with_notes_count'] = cursor.fetchone()[0]
        conn.close()

    print(json.dumps(result, indent=2))
    return result


def get_approved_stories():
    """Output approved stories for vision synthesis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, description, notes FROM story_nodes
        WHERE status = 'approved' ORDER BY id
    ''')
    for row in cursor.fetchall():
        print(f'=== {row[0]}: {row[1]} ===')
        print(row[2])
        if row[3]:
            print(f'Notes: {row[3]}')
        print()
    conn.close()


def get_rejected_stories():
    """Output rejected stories with notes for anti-vision synthesis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, description, notes FROM story_nodes
        WHERE status = 'rejected' AND notes IS NOT NULL AND notes != ''
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
        'rejected': get_rejected_stories
    }
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)
