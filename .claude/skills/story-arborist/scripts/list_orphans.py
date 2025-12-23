#!/usr/bin/env python
"""List orphaned nodes (exist in story_nodes but not in story_paths).

Usage: python list_orphans.py [--ids-only]
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection

def main():
    ids_only = '--ids-only' in sys.argv

    conn = get_connection()
    orphans = conn.execute('''
        SELECT sn.id, sn.title, sn.stage, sn.hold_reason, sn.disposition
        FROM story_nodes sn
        WHERE sn.id != 'root'
          AND NOT EXISTS (
              SELECT 1 FROM story_paths sp WHERE sp.descendant_id = sn.id
          )
        ORDER BY sn.id
    ''').fetchall()
    conn.close()

    if not orphans:
        if not ids_only:
            print("No orphaned nodes found.")
        return 0

    if ids_only:
        for (node_id, _, _, _, _) in orphans:
            print(node_id)
    else:
        print(f"Found {len(orphans)} orphaned node(s):\n")
        for (node_id, title, stage, hold_reason, disposition) in orphans:
            status = disposition or hold_reason or stage
            print(f"  {node_id}: [{status}] {title}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
