import sqlite3
import json
import re

# Re-query to get current state
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

planned = conn.execute("""
    SELECT id, title, description, notes FROM story_nodes
    WHERE stage = 'planned'
      AND hold_reason IS NULL
      AND disposition IS NULL
    ORDER BY updated_at ASC
""").fetchall()

IMPLEMENTED_STAGES = ('implemented', 'ready', 'released')
PLANNED_OR_LATER = ('planned', 'active', 'reviewing', 'verifying', 'implemented', 'ready', 'released')

activated = []
blocked = []
cycles_resolved = []

def get_block_chain(story_id, visited=None):
    """Walk the block chain from a story, return all stories in chain."""
    if visited is None:
        visited = set()
    if story_id in visited:
        return visited
    visited.add(story_id)

    row = conn.execute("""
        SELECT hold_reason FROM story_nodes
        WHERE id = ? AND hold_reason LIKE 'blocked:%'
    """, (story_id,)).fetchone()

    if row:
        blocker_ids_str = row['hold_reason'][8:]
        for bid in blocker_ids_str.split(','):
            bid = bid.strip()
            if bid:
                get_block_chain(bid, visited)
    return visited

for story in planned:
    story_id = story['id']
    text = (story['description'] or '') + ' ' + (story['notes'] or '')

    # Extract dependencies
    dep_pattern = r'(?:depends on|requires|after|needs)\s+(\d+(?:\.\d+)*)|(?<!\d)(\d+\.\d+(?:\.\d+)*)(?!\d)'
    deps = set()
    for match in re.finditer(dep_pattern, text, re.IGNORECASE):
        dep_id = match.group(1) or match.group(2)
        if dep_id and dep_id != story_id:
            deps.add(dep_id)

    # Check dependencies
    blocker_ids = []
    for dep_id in deps:
        dep = conn.execute(
            'SELECT id, stage FROM story_nodes WHERE id = ? AND disposition IS NULL',
            (dep_id,)
        ).fetchone()
        if dep and dep['stage'] not in IMPLEMENTED_STAGES:
            blocker_ids.append(dep_id)

    # Check children
    children = conn.execute("""
        SELECT s.id, s.stage FROM story_nodes s
        JOIN story_paths p ON s.id = p.descendant_id
        WHERE p.ancestor_id = ? AND p.depth = 1
          AND s.disposition IS NULL
    """, (story_id,)).fetchall()

    for child in children:
        if child['stage'] not in PLANNED_OR_LATER:
            blocker_ids.append(child['id'])

    if len(blocker_ids) == 0:
        # ACTIVATE - all deps met
        conn.execute("""
            UPDATE story_nodes
            SET stage = 'active',
                hold_reason = NULL,
                notes = COALESCE(notes || char(10), '') ||
                        'ACTIVATED: All dependencies met. ' || datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (story_id,))
        activated.append({'id': story_id, 'title': story['title']})
    else:
        # Check for cycles before blocking
        cycle_found = False
        cycle_chain = []

        for blocker_id in blocker_ids:
            chain = get_block_chain(blocker_id)
            if story_id in chain:
                cycle_found = True
                cycle_chain = list(chain)
                break

        if cycle_found:
            # Resolve cycle: clear stale blocks in chain
            for chain_id in cycle_chain:
                if chain_id != story_id:
                    conn.execute("""
                        UPDATE story_nodes
                        SET hold_reason = NULL,
                            notes = COALESCE(notes || char(10), '') ||
                                    'CYCLE RESOLVED: Block cleared - newer analysis found reverse dependency. ' ||
                                    datetime('now'),
                            updated_at = datetime('now')
                        WHERE id = ? AND hold_reason LIKE 'blocked:%'
                    """, (chain_id,))
            cycles_resolved.append({
                'story_id': story_id,
                'chain': cycle_chain
            })

        # BLOCK with specific blocker IDs
        blocker_ids_str = ','.join(blocker_ids)
        conn.execute("""
            UPDATE story_nodes
            SET hold_reason = 'blocked:' || ?,
                notes = COALESCE(notes || char(10), '') ||
                        'BLOCKED: Waiting on [' || ? || ']. ' || datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (blocker_ids_str, blocker_ids_str, story_id))
        blocked.append({
            'id': story_id,
            'title': story['title'],
            'blockers': blocker_ids
        })

conn.commit()
print(json.dumps({
    'activated': activated,
    'blocked': blocked,
    'cycles_resolved': cycles_resolved
}, indent=2))
conn.close()
