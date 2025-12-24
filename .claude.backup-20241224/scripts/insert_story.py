#!/usr/bin/env python3
"""Insert a story into the database.

Usage: python .claude/scripts/insert_story.py <id> <parent_id> <title> <description>

Example:
  python .claude/scripts/insert_story.py "1.2.3" "1.2" "User authentication" "As a user, I want to..."
"""
import sqlite3
import sys

DB_PATH = '.claude/data/story-tree.db'


def insert_story(story_id, parent_id, title, description):
    """Insert a new story node with closure table paths."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert the story node
    cursor.execute('''
        INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
        VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
    ''', (story_id, title, description))

    # Insert closure table paths (connect to all ancestors + self)
    cursor.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        SELECT ancestor_id, ?, depth + 1
        FROM story_paths WHERE descendant_id = ?
        UNION ALL SELECT ?, ?, 0
    ''', (story_id, parent_id, story_id, story_id))

    conn.commit()
    conn.close()
    print(f'OK: Inserted story {story_id}')


def update_commit(commit_hash):
    """Update lastAnalyzedCommit metadata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', ?)", (commit_hash,))
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))")
    conn.commit()
    conn.close()
    print(f'OK: Updated lastAnalyzedCommit to {commit_hash}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  insert_story.py <id> <parent_id> <title> <description>')
        print('  insert_story.py --update-commit <commit_hash>')
        sys.exit(1)

    if sys.argv[1] == '--update-commit':
        if len(sys.argv) < 3:
            print('Usage: insert_story.py --update-commit <commit_hash>')
            sys.exit(1)
        update_commit(sys.argv[2])
    else:
        if len(sys.argv) < 5:
            print('Usage: insert_story.py <id> <parent_id> <title> <description>')
            sys.exit(1)
        insert_story(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
