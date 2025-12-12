#!/usr/bin/env python3
"""Import story tree from JSON backup into SQLite database."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

def initialize_database(db_path, schema_path):
    """Create database and apply schema."""
    conn = sqlite3.connect(db_path)

    # Read and execute schema
    with open(schema_path, 'r') as f:
        schema = f.read()
    conn.executescript(schema)

    conn.commit()
    return conn

def insert_node(conn, node, parent_id=None):
    """Recursively insert node and all its children into database."""
    cursor = conn.cursor()

    # Extract data from JSON node
    story_id = node['id']
    story = node['story']
    description = node.get('description', '')
    capacity = node.get('capacity', 3)
    status = node.get('status', 'concept')
    project_path = node.get('projectPath')
    last_implemented = node.get('lastImplemented')

    # Insert into stories table
    cursor.execute('''
        INSERT INTO stories (id, story, description, capacity, status, project_path, last_implemented, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (story_id, story, description, capacity, status, project_path, last_implemented))

    # Insert into closure table
    # First, add self-reference (depth 0)
    cursor.execute('''
        INSERT INTO story_tree (ancestor_id, descendant_id, depth)
        VALUES (?, ?, 0)
    ''', (story_id, story_id))

    # Then, if this node has a parent, copy all ancestor paths from parent and add new paths
    if parent_id:
        cursor.execute('''
            INSERT INTO story_tree (ancestor_id, descendant_id, depth)
            SELECT ancestor_id, ?, depth + 1
            FROM story_tree WHERE descendant_id = ?
        ''', (story_id, parent_id))

    # Process implemented commits
    implemented_commits = node.get('implementedCommits', [])
    for commit_hash in implemented_commits:
        cursor.execute('''
            INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
            VALUES (?, ?, NULL, NULL)
        ''', (story_id, commit_hash))

    # Recursively insert children
    children = node.get('children', [])
    for child in children:
        insert_node(conn, child, story_id)

    conn.commit()

def import_from_json(json_path, db_path, schema_path):
    """Import story tree from JSON backup into SQLite database."""

    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Initialize database
    conn = initialize_database(db_path, schema_path)

    # Insert root node and all its children
    root = data['root']
    insert_node(conn, root)

    # Insert metadata
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('version', '2.0.0'))
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('lastUpdated', data.get('lastUpdated', datetime.now().isoformat())))
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                   ('lastAnalyzedCommit', data.get('lastAnalyzedCommit', '')))

    conn.commit()
    conn.close()

    print(f"Successfully imported story tree from {json_path} to {db_path}")

if __name__ == '__main__':
    # Paths (relative to repository root)
    base_dir = Path(__file__).parent.parent.parent
    json_path = base_dir / 'skills/story-tree/story-tree.json.backup'
    db_path = base_dir / 'data/story-tree.db'
    schema_path = base_dir / 'skills/story-tree/schema.sql'

    import_from_json(json_path, db_path, schema_path)
