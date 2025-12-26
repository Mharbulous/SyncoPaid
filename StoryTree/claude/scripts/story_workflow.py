#!/usr/bin/env python3
"""
Unified story generation workflow for CI automation.
Usage: python .claude/scripts/story_workflow.py [--max-stories N] [--ci]

Reduces token usage by consolidating 8+ separate DB operations into one script.
"""
import sqlite3
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = '.claude/data/story-tree.db'


def get_last_commit():
    """Get last analyzed commit from metadata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_new_commits(last_commit):
    """Get commits since last analysis."""
    if last_commit:
        result = subprocess.run(['git', 'cat-file', '-t', last_commit], capture_output=True)
        if result.returncode != 0:
            last_commit = None

    if last_commit:
        cmd = ['git', 'log', f'{last_commit}..HEAD', '--pretty=format:%h|%s', '--no-merges']
    else:
        cmd = ['git', 'log', '--since=30 days ago', '--pretty=format:%h|%s', '--no-merges']

    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line and '|' in line:
            hash_, msg = line.split('|', 1)
            commits.append({'hash': hash_, 'message': msg})

    newest_commit = commits[0]['hash'] if commits else last_commit
    return commits, newest_commit


def find_priority_target():
    """Find under-capacity node prioritizing shallower nodes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Three-field system: exclude concept stage, held, and disposed stories
    cursor.execute('''
        SELECT s.id, s.title, s.description, s.capacity,
            (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
            (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
            COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
                 JOIN story_nodes child ON sp.descendant_id = child.id
                 WHERE sp.ancestor_id = s.id AND sp.depth = 1
                 AND child.stage IN ('implemented', 'ready', 'released'))) as effective_capacity
        FROM story_nodes s
        WHERE s.stage != 'concept'
          AND s.hold_reason IS NULL
          AND s.disposition IS NULL
          AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
              COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
                   JOIN story_nodes child ON sp.descendant_id = child.id
                   WHERE sp.ancestor_id = s.id AND sp.depth = 1
                   AND child.stage IN ('implemented', 'ready', 'released')))
        ORDER BY node_depth ASC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0], 'title': row[1], 'description': row[2],
            'capacity': row[3], 'child_count': row[4],
            'node_depth': row[5], 'effective_capacity': row[6]
        }
    return None


def get_node_context(node_id):
    """Get children context for the target node."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.id, s.title, s.description, s.stage, s.hold_reason, s.disposition
        FROM story_nodes s
        JOIN story_paths sp ON s.id = sp.descendant_id
        WHERE sp.ancestor_id = ? AND sp.depth = 1
        ORDER BY s.id
    ''', (node_id,))
    children = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return children


def get_next_child_id(parent_id):
    """Get next available child ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id FROM story_nodes s
        JOIN story_paths sp ON s.id = sp.descendant_id
        WHERE sp.ancestor_id = ? AND sp.depth = 1
        ORDER BY CAST(SUBSTR(s.id, LENGTH(?) + 2) AS INTEGER) DESC
        LIMIT 1
    ''', (parent_id, parent_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        last_num = int(row[0].split('.')[-1])
        return f"{parent_id}.{last_num + 1}"
    return f"{parent_id}.1"


def get_stats():
    """Get tree statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM story_nodes')
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE stage = 'implemented'")
    implemented = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE stage = 'concept'")
    concept = cursor.fetchone()[0]
    conn.close()
    return {'total': total, 'implemented': implemented, 'concept': concept}


def update_metadata(newest_commit):
    """Update lastUpdated and lastAnalyzedCommit."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))")
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', ?)", (newest_commit,))
    conn.commit()
    conn.close()


def main():
    ci_mode = '--ci' in sys.argv
    max_stories = 2  # Default for CI

    for i, arg in enumerate(sys.argv):
        if arg == '--max-stories' and i + 1 < len(sys.argv):
            max_stories = int(sys.argv[i + 1])

    # Step 1: Check prerequisites
    if not Path(DB_PATH).exists():
        print('ERROR: Database not found at', DB_PATH)
        sys.exit(1)

    # Step 2: Analyze commits
    last_commit = get_last_commit()
    commits, newest_commit = get_new_commits(last_commit)

    # Step 3: Find priority target
    target = find_priority_target()
    if not target:
        print('NO_CAPACITY: All nodes at capacity')
        sys.exit(0)

    # Step 4: Get context
    children = get_node_context(target['id'])
    next_id = get_next_child_id(target['id'])

    # Output context for Claude to generate story
    output = {
        'target': target,
        'children': children,
        'next_id': next_id,
        'commits_analyzed': len(commits),
        'newest_commit': newest_commit,
        'stats': get_stats()
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
