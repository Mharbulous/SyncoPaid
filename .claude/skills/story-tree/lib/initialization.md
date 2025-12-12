# Story Tree Database Initialization

This document is loaded only when initializing a new story tree database. For regular workflow, see the main SKILL.md.

## When to Use

Initialize a new database when:
- `.claude/data/story-tree.db` does not exist
- User explicitly requests "Initialize story tree"
- Migration from older format is needed

## Step 1: Detect Project Metadata

Read project information from `package.json`:

```bash
# Extract project name and description
python -c "
import json
with open('package.json', 'r') as f:
    pkg = json.load(f)
    print(f'NAME:{pkg.get(\"name\", \"Unknown Project\")}')
    print(f'DESC:{pkg.get(\"description\", \"\")}')
"
```

If `package.json` doesn't exist or lacks description, read from `CLAUDE.md`:

```bash
# Extract project description from CLAUDE.md
grep -A 2 "^## .*Project Overview" CLAUDE.md | grep -v "^##" | grep -v "^--"
```

**Fallback defaults if no metadata found:**
- Title: `"Software Project"`
- Description: `"Software project story tree"`

## Step 2: Initialize Database

**CRITICAL:** The root node should represent **this specific project**, not a multi-app portfolio.

```bash
# Create data directory
mkdir -p .claude/data

# Initialize schema
cat .claude/skills/story-tree/schema.sql | python -c "
import sqlite3
import sys
import json

# Read schema from stdin
schema = sys.stdin.read()

# Connect to database
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Apply schema
cursor.executescript(schema)

# Read project metadata from package.json
try:
    with open('package.json', 'r') as f:
        pkg = json.load(f)
        project_name = pkg.get('name', 'Software Project')
        project_desc = pkg.get('description', '')

        # If no description in package.json, try to extract from CLAUDE.md
        if not project_desc:
            try:
                with open('CLAUDE.md', 'r') as cf:
                    for line in cf:
                        if 'Project:' in line or 'project' in line.lower():
                            project_desc = line.strip()
                            break
            except:
                pass

        # Final fallback
        if not project_desc:
            project_desc = f'{project_name} - Software project story tree'

except FileNotFoundError:
    project_name = 'Software Project'
    project_desc = 'Software project story tree'

# Insert root node (represents THIS project)
# capacity is NULL - uses dynamic calculation: 3 + implemented/ready children
cursor.execute('''
    INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
''', ('root', project_name, project_desc, 'active'))

# Root self-reference in closure table
cursor.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    VALUES ('root', 'root', 0)
''')

# Metadata
cursor.execute(\"INSERT INTO metadata (key, value) VALUES ('version', '2.4.0')\")
cursor.execute(\"INSERT INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))\")

conn.commit()
conn.close()

print(f'Initialized story tree for: {project_name}')
"
```

## Why This Approach?

**ANTI-PATTERN (OLD):** Creating a portfolio-level root ("SaaS Apps for lawyers") with project as child.
- Assumes multi-app portfolio
- Hardcodes business domain
- Creates unnecessary nesting
- Database lives in ONE repo but tracks MANY apps

**CORRECT (NEW):** Project-specific root based on current repository.
- Each repo's `.claude/data/story-tree.db` tracks ONLY that project
- Root represents the actual software being built
- Auto-detects project name from package.json
- No hardcoded assumptions about business domain
