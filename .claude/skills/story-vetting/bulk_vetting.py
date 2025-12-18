#!/usr/bin/env python3
"""
Bulk vetting processor - applies LLM classifications and executes actions.

Uses consolidated database operations from story-tree utility.
"""
import sqlite3
import json
import sys
import os

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import (
    DB_PATH,
    delete_story,
    duplicative_concept,
    block_concept,
    merge_concepts,
)

# Import cache function from vetting_cache
from vetting_cache import store_decision


def apply_decisions(decisions):
    """Apply a list of vetting decisions.

    decisions format: [
        {"id_a": "1.2.3", "id_b": "1.4.5", "classification": "false_positive", "action": "SKIP"},
        ...
    ]
    """
    stats = {
        "deleted": 0,
        "duplicative": 0,
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
            conn = sqlite3.connect(DB_PATH)

            # Cache the decision first (if both stories exist)
            row_a = conn.execute("SELECT id FROM story_nodes WHERE id = ?", (id_a,)).fetchone()
            row_b = conn.execute("SELECT id FROM story_nodes WHERE id = ?", (id_b,)).fetchone()
            if row_a and row_b:
                store_decision(conn, id_a, id_b, classification, action)

            # Execute action
            if action == 'SKIP':
                stats['skipped'] += 1

            elif action == 'DELETE_CONCEPT':
                concept_id = decision.get('concept_id', id_a if id_a > id_b else id_b)
                delete_story(conn, concept_id)
                conn.commit()
                stats['deleted'] += 1
                print(f"  Deleted {concept_id}")

            elif action == 'DUPLICATIVE_CONCEPT':
                concept_id = decision['concept_id']
                duplicate_of_id = decision['conflicting_id']
                duplicative_concept(conn, concept_id, duplicate_of_id)
                conn.commit()
                stats['duplicative'] += 1
                print(f"  Marked {concept_id} as duplicative")

            elif action == 'BLOCK_CONCEPT':
                concept_id = decision['concept_id']
                conflicting_id = decision['conflicting_id']
                block_concept(conn, concept_id, conflicting_id)
                conn.commit()
                stats['blocked'] += 1
                print(f"  Blocked {concept_id}")

            elif action == 'TRUE_MERGE':
                keep_id = decision['keep_id']
                delete_id = decision['delete_id']
                merged_title = decision['merged_title']
                merged_description = decision['merged_description']
                merge_concepts(conn, keep_id, delete_id, merged_title, merged_description)
                conn.commit()
                stats['merged'] += 1
                print(f"  Merged {delete_id} into {keep_id}")

            conn.close()

        except Exception as e:
            stats['errors'] += 1
            print(f"  Error processing {id_a} vs {id_b}: {e}")

    return stats


if __name__ == '__main__':
    # Read decisions from stdin
    decisions = json.load(sys.stdin)
    stats = apply_decisions(decisions)

    print("\nVetting Summary:")
    print(f"  Deleted: {stats['deleted']}")
    print(f"  Duplicative: {stats['duplicative']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Merged: {stats['merged']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
