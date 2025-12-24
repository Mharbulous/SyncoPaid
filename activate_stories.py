import sqlite3
import re
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

# Get all planned stories without holds, ordered by updated_at
planned = conn.execute("""
    SELECT id, title, description, notes FROM story_nodes
    WHERE stage = 'planned'
      AND hold_reason IS NULL
      AND disposition IS NULL
    ORDER BY updated_at ASC
""").fetchall()

print(f"Found {len(planned)} planned stories without holds")

IMPLEMENTED_STAGES = ('implemented', 'ready', 'released')
PLANNED_OR_LATER = ('planned', 'active', 'reviewing', 'verifying', 'implemented', 'ready', 'released')

results = []
for story in planned:
    story_id = story['id']
    text = (story['description'] or '') + ' ' + (story['notes'] or '')

    # Extract dependency IDs (patterns: 1.2, 1.3.1, etc., or explicit 'depends on X')
    dep_pattern = r'(?:depends on|requires|after|needs)\s+(\d+(?:\.\d+)*)|(?<!\d)(\d+\.\d+(?:\.\d+)*)(?!\d)'
    deps = set()
    for match in re.finditer(dep_pattern, text, re.IGNORECASE):
        dep_id = match.group(1) or match.group(2)
        if dep_id and dep_id != story_id:
            deps.add(dep_id)

    # Check dependency stories are implemented
    blocker_ids = []
    for dep_id in deps:
        dep = conn.execute(
            'SELECT id, title, stage FROM story_nodes WHERE id = ? AND disposition IS NULL',
            (dep_id,)
        ).fetchone()
        if dep and dep['stage'] not in IMPLEMENTED_STAGES:
            blocker_ids.append(dep_id)

    # Check all children are at least planned
    children = conn.execute("""
        SELECT s.id, s.title, s.stage FROM story_nodes s
        JOIN story_paths p ON s.id = p.descendant_id
        WHERE p.ancestor_id = ? AND p.depth = 1
          AND s.disposition IS NULL
    """, (story_id,)).fetchall()

    for child in children:
        if child['stage'] not in PLANNED_OR_LATER:
            blocker_ids.append(child['id'])

    ready = len(blocker_ids) == 0
    results.append({
        'id': story_id,
        'title': story['title'],
        'ready': ready,
        'blocker_ids': blocker_ids
    })

print(json.dumps(results, indent=2))
conn.close()
