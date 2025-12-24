#!/usr/bin/env python
"""Create a new story node under a parent.

Usage: python create_node.py <parent_id> --title "..." [--description "..."] [--stage concept] [--capacity N] [--dry-run]

Examples:
    python create_node.py 8 --title "New Feature"                    # Create child of story 8
    python create_node.py root --title "New Epic" --stage approved   # Create new primary epic
    python create_node.py 15 --title "Task" --capacity 2 --dry-run   # Preview creation
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, get_next_child_id


def main():
    parser = argparse.ArgumentParser(
        description='Create a new story node under a parent.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_node.py 8 --title "New Feature"
  python create_node.py root --title "New Epic" --stage approved
  python create_node.py 15 --title "Task" --capacity 2 --dry-run
"""
    )
    parser.add_argument('parent_id', help='Parent story ID (use "root" for top level)')
    parser.add_argument('--title', required=True, help='Title for the new node')
    parser.add_argument('--description', default='', help='Description for the new node')
    parser.add_argument('--stage', default='concept', help='Stage (default: concept)')
    parser.add_argument('--capacity', type=int, help='Story capacity/points')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')

    args = parser.parse_args()

    conn = get_connection()

    # Validate parent exists
    parent = conn.execute(
        'SELECT id, title FROM story_nodes WHERE id = ?', (args.parent_id,)
    ).fetchone()

    if not parent:
        print(f"Error: Parent '{args.parent_id}' not found")
        conn.close()
        return 1

    # Generate new ID
    new_id = get_next_child_id(conn, args.parent_id)

    parent_display = parent[1] if args.parent_id != 'root' else 'Root'
    print(f"Creating new node:")
    print(f"  ID: {new_id}")
    print(f"  Parent: {args.parent_id} ({parent_display})")
    print(f"  Title: {args.title}")
    if args.description:
        print(f"  Description: {args.description}")
    print(f"  Stage: {args.stage}")
    if args.capacity:
        print(f"  Capacity: {args.capacity}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    try:
        # Insert the new node
        conn.execute('''
            INSERT INTO story_nodes (id, title, description, stage, capacity)
            VALUES (?, ?, ?, ?, ?)
        ''', (new_id, args.title, args.description, args.stage, args.capacity))

        # Insert self-path (depth=0)
        conn.execute('''
            INSERT INTO story_paths (ancestor_id, descendant_id, depth)
            VALUES (?, ?, 0)
        ''', (new_id, new_id))

        # Insert paths to all ancestors (copy parent's paths with depth+1)
        conn.execute('''
            INSERT INTO story_paths (ancestor_id, descendant_id, depth)
            SELECT ancestor_id, ?, depth + 1
            FROM story_paths WHERE descendant_id = ?
        ''', (new_id, args.parent_id))

        conn.commit()
        print(f"\nSuccess: Created node {new_id}")

    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()
        conn.close()
        return 1
    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
