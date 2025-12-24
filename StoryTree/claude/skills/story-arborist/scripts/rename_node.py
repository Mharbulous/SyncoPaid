#!/usr/bin/env python
"""Rename a story node and all its descendants.

Usage: python rename_node.py <old_id> <new_id> [--dry-run]

Examples:
    python rename_node.py 8.6 16              # Rename decimal to integer
    python rename_node.py 15 99               # Renumber a top-level epic
    python rename_node.py 1.5 1.99 --dry-run  # Preview rename
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, rename_story

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = '--dry-run' in sys.argv

    if len(args) != 2:
        print("Usage: python rename_node.py <old_id> <new_id> [--dry-run]")
        print("\nExamples:")
        print("  python rename_node.py 8.6 16        # Rename decimal to integer")
        print("  python rename_node.py 1.5 1.99      # Renumber within parent")
        return 1

    old_id, new_id = args

    conn = get_connection()

    # Check source exists
    story = conn.execute(
        'SELECT id, title FROM story_nodes WHERE id = ?', (old_id,)
    ).fetchone()

    if not story:
        print(f"Error: Story '{old_id}' not found")
        conn.close()
        return 1

    # Check target doesn't exist
    conflict = conn.execute(
        'SELECT id FROM story_nodes WHERE id = ?', (new_id,)
    ).fetchone()

    if conflict:
        print(f"Error: Story '{new_id}' already exists")
        conn.close()
        return 1

    # Count descendants
    descendants = conn.execute('''
        SELECT COUNT(*) FROM story_paths
        WHERE ancestor_id = ? AND depth > 0
    ''', (old_id,)).fetchone()[0]

    print(f"Renaming: {old_id} -> {new_id}")
    print(f"Title: {story[1]}")
    print(f"Descendants to update: {descendants}")

    if dry_run:
        # Preview what will be renamed
        if descendants > 0:
            desc_list = conn.execute('''
                SELECT descendant_id FROM story_paths
                WHERE ancestor_id = ? AND depth > 0
                ORDER BY depth, descendant_id
            ''', (old_id,)).fetchall()
            print("\nDescendants that will be renamed:")
            for (desc_id,) in desc_list[:10]:
                if desc_id.startswith(old_id + '.'):
                    suffix = desc_id[len(old_id):]
                    print(f"  {desc_id} -> {new_id}{suffix}")
            if descendants > 10:
                print(f"  ... and {descendants - 10} more")
        print("\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    try:
        conn.execute('PRAGMA foreign_keys = OFF')
        renames = rename_story(conn, old_id, new_id)
        conn.commit()
        print(f"\nSuccess: Renamed {len(renames)} node(s)")
        for old, new in renames[:10]:
            print(f"  {old} -> {new}")
        if len(renames) > 10:
            print(f"  ... and {len(renames) - 10} more")
    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()
        conn.close()
        return 1
    finally:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
