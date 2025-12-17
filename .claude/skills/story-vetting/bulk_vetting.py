#!/usr/bin/env python3
"""
Bulk vetting processor - applies LLM classifications and executes actions.
"""
import sqlite3
import json
import sys
from datetime import datetime

def cache_decision(id_a, id_b, classification, action):
    """Cache a vetting decision."""
    if id_a > id_b:
        id_a, id_b = id_b, id_a
    pair_key = f"{id_a}|{id_b}"

    conn = sqlite3.connect('.claude/data/story-tree.db')

    # Get versions (handle deleted stories)
    cursor_a = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_a,))
    cursor_b = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (id_b,))
    result_a = cursor_a.fetchone()
    result_b = cursor_b.fetchone()

    version_a = result_a[0] if result_a else 1
    version_b = result_b[0] if result_b else 1

    conn.execute("""
        INSERT OR REPLACE INTO vetting_decisions
        (pair_key, story_a_id, story_b_id, story_a_version, story_b_version, classification, action_taken, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pair_key, id_a, id_b, version_a, version_b, classification, action, datetime.now().isoformat()))

    conn.commit()
    conn.close()

def apply_decisions(decisions):
    """Apply a list of vetting decisions.

    decisions format: [
        {"id_a": "1.2.3", "id_b": "1.4.5", "classification": "false_positive", "action": "SKIP"},
        ...
    ]
    """
    stats = {
        "deleted": 0,
        "rejected": 0,
        "blocked": 0,
        "merged": 0,
        "skipped": 0,
        "errors": 0
    }

    for decision in decisions:
        id_a = decision['id_a']
        id_b = decision['id_b']
        classification = decision['classification']
        action = decision['action']

        try:
            # Cache the decision first
            cache_decision(id_a, id_b, classification, action)

            # Execute action
            if action == 'SKIP':
                stats['skipped'] += 1

            elif action == 'DELETE_CONCEPT':
                concept_id = decision.get('concept_id', id_a if id_a > id_b else id_b)
                conn = sqlite3.connect('.claude/data/story-tree.db')
                conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (concept_id,))
                conn.execute('DELETE FROM story_nodes WHERE id = ?', (concept_id,))
                conn.commit()
                conn.close()
                stats['deleted'] += 1
                print(f"  ✓ Deleted {concept_id}")

            elif action == 'REJECT_CONCEPT':
                concept_id = decision['concept_id']
                conflicting_id = decision['conflicting_id']
                conn = sqlite3.connect('.claude/data/story-tree.db')
                conn.execute('''
                    UPDATE story_nodes
                    SET status = 'rejected',
                        notes = COALESCE(notes || char(10), '') || 'Conflicts with story node ' || ?
                    WHERE id = ?
                ''', (conflicting_id, concept_id))
                conn.commit()
                conn.close()
                stats['rejected'] += 1
                print(f"  ✓ Rejected {concept_id}")

            elif action == 'BLOCK_CONCEPT':
                concept_id = decision['concept_id']
                conflicting_id = decision['conflicting_id']
                conn = sqlite3.connect('.claude/data/story-tree.db')
                conn.execute('''
                    UPDATE story_nodes
                    SET status = 'blocked',
                        notes = COALESCE(notes || char(10), '') || 'Blocked due to conflict with story node ' || ?
                    WHERE id = ?
                ''', (conflicting_id, concept_id))
                conn.commit()
                conn.close()
                stats['blocked'] += 1
                print(f"  ✓ Blocked {concept_id}")

            elif action == 'TRUE_MERGE':
                keep_id = decision['keep_id']
                delete_id = decision['delete_id']
                merged_title = decision['merged_title']
                merged_description = decision['merged_description']

                conn = sqlite3.connect('.claude/data/story-tree.db')
                conn.execute('''
                    UPDATE story_nodes
                    SET title = ?, description = ?,
                        notes = COALESCE(notes || char(10), '') || 'Merged from story node ' || ?
                    WHERE id = ?
                ''', (merged_title, merged_description, delete_id, keep_id))
                conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (delete_id,))
                conn.execute('DELETE FROM story_nodes WHERE id = ?', (delete_id,))
                conn.commit()
                conn.close()
                stats['merged'] += 1
                print(f"  ✓ Merged {delete_id} into {keep_id}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  ✗ Error processing {id_a} vs {id_b}: {e}")

    return stats

if __name__ == '__main__':
    # Read decisions from stdin
    decisions = json.load(sys.stdin)
    stats = apply_decisions(decisions)

    print("\nVetting Summary:")
    print(f"  Deleted: {stats['deleted']}")
    print(f"  Rejected: {stats['rejected']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Merged: {stats['merged']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
