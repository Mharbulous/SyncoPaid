#!/usr/bin/env python
"""Fix orphaned nodes by rebuilding their story_paths entries.

Usage: python fix_orphans.py [--dry-run]

Finds all orphaned nodes (exist in story_nodes but not in story_paths)
and rebuilds their closure table entries based on their ID hierarchy.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, rebuild_paths

def main():
    dry_run = '--dry-run' in sys.argv

    conn = get_connection()

    # Find orphaned nodes
    orphans = conn.execute('''
        SELECT sn.id, sn.title
        FROM story_nodes sn
        WHERE sn.id != 'root'
          AND NOT EXISTS (
              SELECT 1 FROM story_paths sp WHERE sp.descendant_id = sn.id
          )
        ORDER BY LENGTH(sn.id), sn.id
    ''').fetchall()

    if not orphans:
        print("No orphaned nodes found.")
        conn.close()
        return 0

    print(f"Found {len(orphans)} orphaned node(s):\n")
    for (node_id, title) in orphans:
        print(f"  {node_id}: {title}")

    if dry_run:
        print("\n[DRY RUN] No changes made.")
        conn.close()
        return 0

    print("\nRebuilding paths...")
    fixed = 0
    errors = []

    for (node_id, title) in orphans:
        try:
            rebuild_paths(conn, node_id)
            fixed += 1
            print(f"  Fixed: {node_id}")
        except Exception as e:
            errors.append((node_id, str(e)))
            print(f"  Error: {node_id} - {e}")

    conn.commit()
    conn.close()

    print(f"\nFixed {fixed}/{len(orphans)} orphaned node(s)")
    if errors:
        print(f"Errors: {len(errors)}")
        for (node_id, err) in errors:
            print(f"  {node_id}: {err}")

    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())
