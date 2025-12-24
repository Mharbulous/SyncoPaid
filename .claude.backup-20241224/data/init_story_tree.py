#!/usr/bin/env python3
"""Initialize story tree database for SyncoPaid project."""
import sqlite3
import os
import re

# Read schema
schema_path = '.claude/skills/story-tree/references/schema.sql'
with open(schema_path, 'r') as f:
    schema = f.read()

# Connect to database
db_path = '.claude/data/story-tree.db'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Apply schema
cursor.executescript(schema)

# Extract project info from CLAUDE.md
project_name = 'SyncoPaid'
project_desc = 'Windows 11 desktop application for automatic window activity capture'

try:
    with open('CLAUDE.md', 'r', encoding='utf-8') as f:
        content = f.read()
        # Look for project description in first few paragraphs
        match = re.search(r'LawTime Tracker.*?(?:application|app).*?\.', content, re.IGNORECASE)
        if match:
            project_desc = match.group(0)
        else:
            # Fallback: look for ## Project Overview section
            match = re.search(r'## Project Overview\s+(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if match:
                first_sentence = match.group(1).strip().split('.')[0] + '.'
                project_desc = first_sentence
except FileNotFoundError:
    pass

# Insert root node (represents THIS project)
# Uses three-field system: stage/hold_reason/disposition (status column removed)
cursor.execute('''
    INSERT INTO story_nodes (id, title, description, capacity, stage, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
''', ('root', project_name, project_desc, 10, 'active'))

# Root self-reference in closure table
cursor.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    VALUES ('root', 'root', 0)
''')

# Metadata
cursor.execute("INSERT INTO metadata (key, value) VALUES ('version', '2.0.0')")
cursor.execute("INSERT INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))")

conn.commit()
conn.close()

print(f'[OK] Initialized story tree for: {project_name}')
print(f'[OK] Description: {project_desc}')
print(f'[OK] Database: {db_path}')
