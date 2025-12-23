#!/usr/bin/env python
"""Move a story node to a new parent.

Usage: python move_node.py <story_id> <new_parent_id> [--dry-run]

Examples:
    python move_node.py 8.6 root           # Move 8.6 to root level (becomes integer ID)
    python move_node.py 15.3 8             # Move 15.3 under story 8
    python move_node.py 1.2.5 1.3 --dry-run  # Preview move without applying
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, move_story, get_next_child_id

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = '--dry-run' in sys.argv

    if len(args) != 2:
        print("Usage: python move_node.py <story_id> <new_parent_id> [--dry-run]")
        print("\nExamples:")
        print("  python move_node.py 8.6 root       # Move to root (becomes integer ID)")
        print("  python move_node.py 15.3 8         # Move under story 8")
        return 1

    story_id, new_parent_id = args

    conn = get_connection()

    # Preview what will happen
    story = conn.execute(
        'SELECT title FROM story_nodes WHERE id = ?', (story_id,)
    ).fetchone()

    if not story:
        print(f"Error: Story '{story_id}' not found")
        conn.close()
        return 1

    parent = conn.execute(
        'SELECT title FROM story_nodes WHERE id = ?', (new_parent_id,)
    ).fetchone()

    if not parent:
        print(f"Error: Parent '{new_parent_id}' not found")
        conn.close()
        return 1

    # Calculate what the new ID will be
    projected_id = get_next_child_id(conn, new_parent_id)

    print(f"Moving: {story_id} ({story[0]})")
    print(f"To parent: {new_parent_id} ({parent[0] if new_parent_id != 'root' else 'Root'})")
    print(f"New ID will be: {projected_id}")

    if dry_run:
        print("\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    try:
        conn.execute('PRAGMA foreign_keys = OFF')
        new_id = move_story(conn, story_id, new_parent_id)
        conn.commit()
        print(f"\nSuccess: {story_id} -> {new_id}")
    except ValueError as e:
        print(f"\nError: {e}")
        conn.close()
        return 1
    finally:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
