#!/usr/bin/env python
"""Rebuild story_paths closure table for a node (and optionally descendants).

Usage: python rebuild_paths.py <story_id> [--recursive] [--dry-run]

Examples:
    python rebuild_paths.py 8.6              # Rebuild paths for single node
    python rebuild_paths.py 8 --recursive    # Rebuild node and all descendants
    python rebuild_paths.py root --recursive # Rebuild entire tree
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, rebuild_paths, rebuild_paths_recursive

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    recursive = '--recursive' in sys.argv
    dry_run = '--dry-run' in sys.argv

    if len(args) != 1:
        print("Usage: python rebuild_paths.py <story_id> [--recursive] [--dry-run]")
        print("\nExamples:")
        print("  python rebuild_paths.py 8.6              # Single node")
        print("  python rebuild_paths.py 8 --recursive    # Node and descendants")
        print("  python rebuild_paths.py root --recursive # Entire tree")
        return 1

    story_id = args[0]

    conn = get_connection()

    # Check node exists
    story = conn.execute(
        'SELECT id, title FROM story_nodes WHERE id = ?', (story_id,)
    ).fetchone()

    if not story:
        print(f"Error: Story '{story_id}' not found")
        conn.close()
        return 1

    # Count affected nodes
    if recursive:
        if story_id == 'root':
            count = conn.execute(
                "SELECT COUNT(*) FROM story_nodes WHERE id != 'root'"
            ).fetchone()[0]
        else:
            count = conn.execute('''
                SELECT COUNT(*) FROM story_nodes
                WHERE id = ? OR id LIKE ?
            ''', (story_id, story_id + '.%')).fetchone()[0]
    else:
        count = 1

    mode = "recursive" if recursive else "single node"
    print(f"Rebuilding paths for: {story_id} ({mode})")
    print(f"Nodes affected: {count}")

    if dry_run:
        print("\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    try:
        if recursive:
            rebuilt = rebuild_paths_recursive(conn, story_id)
            print(f"\nSuccess: Rebuilt paths for {rebuilt} node(s)")
        else:
            rebuild_paths(conn, story_id)
            print(f"\nSuccess: Rebuilt paths for {story_id}")
        conn.commit()
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
