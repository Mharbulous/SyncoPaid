#!/usr/bin/env python3
"""
Execute vetting actions on the database.
"""
import sqlite3
import sys

MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}
BLOCK_STATUSES = {'rejected', 'infeasible', 'broken', 'pending', 'blocked'}

def _cache_decision_internal(conn, id_a, id_b, classification, action):
    """Internal function to cache decision with existing connection."""
    # Normalize pair key (smaller ID first)
    if id_a > id_b:
        id_a, id_b = id_b, id_a
    pair_key = f"{id_a}|{id_b}"

    # Get versions
    cursor_a = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_a,))
    cursor_b = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_b,))
    result_a = cursor_a.fetchone()
    result_b = cursor_b.fetchone()

    if result_a and result_b:
        version_a = result_a[0]
        version_b = result_b[0]

        conn.execute("""
            INSERT OR REPLACE INTO vetting_decisions
            (pair_key, story_a_id, story_b_id, story_a_version, story_b_version, classification, action_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pair_key, id_a, id_b, version_a, version_b, classification, action))

def delete_concept(concept_id, conflicting_id=None, cache=True):
    """Delete a concept story from the database."""
    conn = sqlite3.connect('.claude/data/story-tree.db')

    # Cache decision before deleting
    if cache and conflicting_id:
        _cache_decision_internal(conn, concept_id, conflicting_id, 'duplicate', 'DELETE_CONCEPT')

    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (concept_id,))
    conn.execute('DELETE FROM story_nodes WHERE id = ?', (concept_id,))
    conn.commit()
    conn.close()
    return f"✓ Deleted concept {concept_id}"

def reject_concept(concept_id, conflicting_id):
    """Set a concept to rejected disposition with conflict note."""
    conn = sqlite3.connect('.claude/data/story-tree.db')
    conn.execute('''
        UPDATE story_nodes
        SET disposition = 'rejected',
            notes = COALESCE(notes || char(10), '') || 'Conflicts with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    conn.commit()
    conn.close()
    return f"✓ Rejected concept {concept_id} (conflicts with {conflicting_id})"

def block_concept(concept_id, conflicting_id):
    """Set a concept to blocked hold_reason with conflict note (stage preserved)."""
    conn = sqlite3.connect('.claude/data/story-tree.db')
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'blocked', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Blocked due to conflict with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    conn.commit()
    conn.close()
    return f"✓ Blocked concept {concept_id} (conflicts with {conflicting_id})"

def defer_concept(concept_id, conflicting_id):
    """Set a concept to pending hold_reason for later human review (CI mode). Stage preserved."""
    conn = sqlite3.connect('.claude/data/story-tree.db')
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'pending', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Scope overlap with ' || ? || ' - needs human review'
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    conn.commit()
    conn.close()
    return f"✓ Deferred concept {concept_id} to pending (scope overlap with {conflicting_id})"

def true_merge(keep_id, delete_id, merged_title, merged_description):
    """Merge two stories, keeping one and deleting the other."""
    conn = sqlite3.connect('.claude/data/story-tree.db')

    # Update the kept story
    conn.execute('''
        UPDATE story_nodes
        SET title = ?, description = ?,
            notes = COALESCE(notes || char(10), '') || 'Merged from story node ' || ?
        WHERE id = ?
    ''', (merged_title, merged_description, delete_id, keep_id))

    # Delete the other story
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (delete_id,))
    conn.execute('DELETE FROM story_nodes WHERE id = ?', (delete_id,))

    conn.commit()
    conn.close()
    return f"✓ Merged {delete_id} into {keep_id}"

def cache_decision(id_a, id_b, classification, action):
    """Cache a vetting decision."""
    # Normalize pair key (smaller ID first)
    if id_a > id_b:
        id_a, id_b = id_b, id_a
    pair_key = f"{id_a}|{id_b}"

    conn = sqlite3.connect('.claude/data/story-tree.db')

    # Get versions - check if stories exist first
    row_a = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_a,)).fetchone()
    row_b = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_b,)).fetchone()

    if not row_a or not row_b:
        conn.close()
        # Skip caching if stories don't exist (may have been deleted)
        return

    version_a = row_a[0]
    version_b = row_b[0]

    # Get current UTC timestamp in ISO format
    from datetime import datetime, timezone
    decided_at = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT OR REPLACE INTO vetting_decisions
        (pair_key, story_a_id, story_b_id, story_a_version, story_b_version, classification, action_taken, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pair_key, id_a, id_b, version_a, version_b, classification, action, decided_at))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    action = sys.argv[1]

    if action == 'delete':
        concept_id = sys.argv[2]
        print(delete_concept(concept_id))

    elif action == 'reject':
        concept_id = sys.argv[2]
        conflicting_id = sys.argv[3]
        print(reject_concept(concept_id, conflicting_id))

    elif action == 'block':
        concept_id = sys.argv[2]
        conflicting_id = sys.argv[3]
        print(block_concept(concept_id, conflicting_id))

    elif action == 'defer':
        concept_id = sys.argv[2]
        conflicting_id = sys.argv[3]
        print(defer_concept(concept_id, conflicting_id))

    elif action == 'merge':
        keep_id = sys.argv[2]
        delete_id = sys.argv[3]
        merged_title = sys.argv[4]
        merged_description = sys.argv[5]
        print(true_merge(keep_id, delete_id, merged_title, merged_description))

    elif action == 'cache':
        id_a = sys.argv[2]
        id_b = sys.argv[3]
        classification = sys.argv[4]
        action_taken = sys.argv[5]
        cache_decision(id_a, id_b, classification, action_taken)
        print(f"✓ Cached decision for {id_a}|{id_b}: {classification} -> {action_taken}")
