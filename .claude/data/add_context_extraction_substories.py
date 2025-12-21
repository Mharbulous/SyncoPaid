"""Add context extraction substories to story tree."""
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Define the new substories under 1.6 (Enhanced Context Extraction)
substories = [
    {
        'id': '1.6.1',
        'parent_id': '1.6',
        'title': 'URL Extraction from Browser Window Titles',
        'description': '''As a lawyer using AI to categorize my time
I want URLs extracted from browser window titles
So that the AI knows which websites I'm researching for client matters

Acceptance Criteria:
- Extract URLs from Chrome window titles
- Extract URLs from Edge window titles
- Extract URLs from Firefox window titles
- Handle browser windows without URLs gracefully''',
        'stage': 'planned'
    },
    {
        'id': '1.6.2',
        'parent_id': '1.6',
        'title': 'Outlook Email Subject Extraction',
        'description': '''As a lawyer using AI to categorize my time
I want email subjects extracted from Outlook window titles
So that the AI can match email activities to client matters

Acceptance Criteria:
- Extract subject from Outlook inbox view format
- Extract subject from Outlook message window format
- Return None for generic inbox without specific subject
- Handle non-Outlook apps gracefully''',
        'stage': 'planned'
    },
    {
        'id': '1.6.3',
        'parent_id': '1.6',
        'title': 'Office File Path Extraction',
        'description': '''As a lawyer using AI to categorize my time
I want file paths extracted from Office application window titles
So that the AI can match document work to client matter folders

Acceptance Criteria:
- Extract file paths from Word window titles
- Extract file paths from Excel window titles
- Extract file paths from PowerPoint window titles
- Handle filename-only titles (no full path)
- Return None for non-Office apps''',
        'stage': 'planned'
    },
    {
        'id': '1.6.4',
        'parent_id': '1.6',
        'title': 'Unified Context Extraction Function',
        'description': '''As a developer integrating context extraction
I want a single entry point function that handles all app types
So that the tracker can call one function regardless of which app is active

Acceptance Criteria:
- Route browsers to URL extraction
- Route Outlook to subject extraction
- Route Office apps to filepath extraction
- Return None for unknown apps
- Handle None inputs gracefully''',
        'stage': 'planned'
    },
    {
        'id': '1.6.5',
        'parent_id': '1.6',
        'title': 'Tracker Integration for Context Extraction',
        'description': '''As a lawyer using AI to categorize my time
I want extracted context automatically included in activity events
So that the AI has rich data for accurate matter matching

Acceptance Criteria:
- get_active_window() returns url key with extracted context
- TrackerLoop state dict includes url field
- ActivityEvent includes extracted context in url field
- Debug logging for extraction attempts''',
        'stage': 'planned'
    }
]

# Insert each substory
for story in substories:
    story_id = story['id']
    parent_id = story['parent_id']

    # Check if story already exists
    cursor.execute("SELECT id FROM story_nodes WHERE id = ?", (story_id,))
    if cursor.fetchone():
        print(f"Story {story_id} already exists, skipping")
        continue

    # Insert story into story_nodes
    cursor.execute('''
        INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (story_id, story['title'], story['description'], story['stage']))

    # Add to closure table (story_paths) - first add self-reference
    cursor.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        VALUES (?, ?, 0)
    ''', (story_id, story_id))

    # Add paths from all ancestors of parent to this new node
    cursor.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        SELECT ancestor_id, ?, depth + 1
        FROM story_paths
        WHERE descendant_id = ?
    ''', (story_id, parent_id))

    print(f"Inserted story {story_id}: {story['title']}")

# Update the parent story 1.6 stage to 'active' since it now has children
cursor.execute("UPDATE story_nodes SET stage = 'active' WHERE id = '1.6' AND stage = 'planned'")
if cursor.rowcount > 0:
    print("Updated parent 1.6 to 'active' stage")

conn.commit()
conn.close()

print('\nSubstories added successfully!')
