#!/usr/bin/env python
"""Bulk reparent multiple nodes to a new parent.

Usage: python bulk_reparent.py <new_parent_id> <story_id1> [story_id2] ... [--dry-run]

Examples:
    python bulk_reparent.py root 8.6 8.7 8.8   # Move all to root level
    python bulk_reparent.py 15 1.2 1.3 1.4     # Move multiple under story 15
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, move_story

def main():
    dry_run = '--dry-run' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    if len(args) < 2:
        print("Usage: python bulk_reparent.py <new_parent_id> <story_id1> [story_id2] ... [--dry-run]")
        print("\nExamples:")
        print("  python bulk_reparent.py root 8.6 8.7 8.8   # Move all to root level")
        print("  python bulk_reparent.py 15 1.2 1.3 1.4     # Move multiple under story 15")
        return 1

    new_parent_id = args[0]
    story_ids = args[1:]

    conn = get_connection()

    # Validate parent exists
    parent = conn.execute(
        'SELECT title FROM story_nodes WHERE id = ?', (new_parent_id,)
    ).fetchone()

    if not parent:
        print(f"Error: Parent '{new_parent_id}' not found")
        conn.close()
        return 1

    parent_name = parent[0] if new_parent_id != 'root' else 'Root'
    print(f"Target parent: {new_parent_id} ({parent_name})")
    print(f"Stories to move: {len(story_ids)}\n")

    # Validate all stories exist
    invalid = []
    for story_id in story_ids:
        exists = conn.execute(
            'SELECT 1 FROM story_nodes WHERE id = ?', (story_id,)
        ).fetchone()
        if not exists:
            invalid.append(story_id)

    if invalid:
        print("Error: Following stories not found:")
        for sid in invalid:
            print(f"  - {sid}")
        conn.close()
        return 1

    if dry_run:
        print("Would move:")
        for story_id in story_ids:
            title = conn.execute(
                'SELECT title FROM story_nodes WHERE id = ?', (story_id,)
            ).fetchone()[0]
            print(f"  {story_id}: {title}")
        print(f"\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    # Perform moves
    conn.execute('PRAGMA foreign_keys = OFF')
    results = []
    errors = []

    for story_id in story_ids:
        try:
            new_id = move_story(conn, story_id, new_parent_id)
            results.append((story_id, new_id))
            print(f"  {story_id} -> {new_id}")
        except ValueError as e:
            errors.append((story_id, str(e)))
            print(f"  Error: {story_id} - {e}")

    conn.commit()
    conn.execute('PRAGMA foreign_keys = ON')
    conn.close()

    print(f"\nMoved {len(results)}/{len(story_ids)} stories successfully")
    if errors:
        print(f"Errors: {len(errors)}")

    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())
