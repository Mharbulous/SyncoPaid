import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

# Find all planned stories with recorded blockers
blocked_stories = conn.execute("""
    SELECT id, title, hold_reason
    FROM story_nodes
    WHERE stage = 'planned'
      AND hold_reason LIKE 'blocked:%'
      AND disposition IS NULL
""").fetchall()

unblocked = []
still_blocked = []

for story in blocked_stories:
    # Parse blocker IDs from hold_reason (format: 'blocked:1.2.1,1.3.4')
    blocker_ids_str = story['hold_reason'][8:]  # Remove 'blocked:' prefix
    blocker_ids = [bid.strip() for bid in blocker_ids_str.split(',') if bid.strip()]

    # Check if ALL blockers are resolved (implemented, ready, released, or disposed)
    placeholders = ','.join(['?' for _ in blocker_ids])
    unresolved = conn.execute(f"""
        SELECT id, stage FROM story_nodes
        WHERE id IN ({placeholders})
          AND disposition IS NULL
          AND stage NOT IN ('implemented', 'ready', 'released')
    """, blocker_ids).fetchall()

    if len(unresolved) == 0:
        # All blockers resolved - clear hold_reason
        conn.execute("""
            UPDATE story_nodes
            SET hold_reason = NULL,
                notes = COALESCE(notes || char(10), '') ||
                        'UNBLOCKED: Recorded blockers [' || ? || '] resolved. ' ||
                        datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (blocker_ids_str, story['id']))
        unblocked.append({'id': story['id'], 'title': story['title'], 'blockers': blocker_ids})
    else:
        still_blocked.append({
            'id': story['id'],
            'title': story['title'],
            'blockers': blocker_ids,
            'unresolved': [{'id': u['id'], 'stage': u['stage']} for u in unresolved]
        })

conn.commit()
print(json.dumps({'unblocked': unblocked, 'still_blocked': still_blocked}, indent=2))
conn.close()
