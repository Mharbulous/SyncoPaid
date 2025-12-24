#!/usr/bin/env python3
"""
Execute vetting actions on the database.

Uses consolidated database operations from story-tree utility.
"""
import sqlite3
import sys
import os

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import (
    DB_PATH,
    MERGEABLE_STATUSES,
    BLOCK_STATUSES,
    make_pair_key,
    get_story_version,
    delete_story as _delete_story,
    duplicative_concept as _duplicative_concept,
    block_concept as _block_concept,
    defer_concept as _defer_concept,
    merge_concepts as _merge_concepts,
)

# Import cache function from vetting_cache
from vetting_cache import store_decision


def delete_concept(concept_id, conflicting_id=None, cache=True):
    """Delete a concept story from the database."""
    conn = sqlite3.connect(DB_PATH)

    # Cache decision before deleting
    if cache and conflicting_id:
        store_decision(conn, concept_id, conflicting_id, 'duplicate', 'DELETE_CONCEPT')

    _delete_story(conn, concept_id)
    conn.commit()
    conn.close()
    return f"Deleted concept {concept_id}"


def duplicative_concept(concept_id, duplicate_of_id):
    """Set a concept to duplicative disposition (algorithm detected duplicate/overlap)."""
    conn = sqlite3.connect(DB_PATH)
    _duplicative_concept(conn, concept_id, duplicate_of_id)
    conn.commit()
    conn.close()
    return f"Marked concept {concept_id} as duplicative (duplicates {duplicate_of_id})"


def block_concept(concept_id, conflicting_id):
    """Set a concept to blocked hold_reason with conflict note (stage preserved)."""
    conn = sqlite3.connect(DB_PATH)
    _block_concept(conn, concept_id, conflicting_id)
    conn.commit()
    conn.close()
    return f"Blocked concept {concept_id} (conflicts with {conflicting_id})"


def defer_concept(concept_id, conflicting_id):
    """Set a concept to refine hold_reason due to scope overlap. Stage preserved."""
    conn = sqlite3.connect(DB_PATH)
    _defer_concept(conn, concept_id, conflicting_id)
    conn.commit()
    conn.close()
    return f"Set concept {concept_id} to refine (scope overlap with {conflicting_id})"


def true_merge(keep_id, delete_id, merged_title, merged_description):
    """Merge two stories, keeping one and deleting the other."""
    conn = sqlite3.connect(DB_PATH)
    _merge_concepts(conn, keep_id, delete_id, merged_title, merged_description)
    conn.commit()
    conn.close()
    return f"Merged {delete_id} into {keep_id}"


def cache_decision(id_a, id_b, classification, action):
    """Cache a vetting decision."""
    conn = sqlite3.connect(DB_PATH)

    # Check if stories exist first
    row_a = conn.execute("SELECT id FROM story_nodes WHERE id = ?", (id_a,)).fetchone()
    row_b = conn.execute("SELECT id FROM story_nodes WHERE id = ?", (id_b,)).fetchone()

    if not row_a or not row_b:
        conn.close()
        # Skip caching if stories don't exist (may have been deleted)
        return

    store_decision(conn, id_a, id_b, classification, action)
    conn.close()


if __name__ == '__main__':
    action = sys.argv[1]

    if action == 'delete':
        concept_id = sys.argv[2]
        print(delete_concept(concept_id))

    elif action == 'duplicative':
        concept_id = sys.argv[2]
        duplicate_of_id = sys.argv[3]
        print(duplicative_concept(concept_id, duplicate_of_id))

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
        print(f"Cached decision for {id_a}|{id_b}: {classification} -> {action_taken}")
