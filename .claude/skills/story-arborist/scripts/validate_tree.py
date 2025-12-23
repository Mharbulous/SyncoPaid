#!/usr/bin/env python
"""Validate story tree structure and report issues.

Usage: python validate_tree.py [--json]
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'story-tree', 'utility'))
from story_db_common import get_connection, validate_tree_structure

def main():
    output_json = '--json' in sys.argv

    conn = get_connection()
    issues = validate_tree_structure(conn)
    conn.close()

    total_issues = sum(len(v) for v in issues.values())

    if output_json:
        print(json.dumps(issues, indent=2))
    else:
        if total_issues == 0:
            print("Tree structure is valid. No issues found.")
        else:
            print(f"Found {total_issues} structural issue(s):\n")

            if issues['orphaned_nodes']:
                print("ORPHANED NODES (missing from story_paths):")
                for item in issues['orphaned_nodes']:
                    print(f"  - {item['id']}: {item['title']}")
                print()

            if issues['invalid_root_children']:
                print("INVALID ROOT CHILDREN (decimal ID at root level):")
                for item in issues['invalid_root_children']:
                    print(f"  - {item['id']}: {item['reason']}")
                print()

            if issues['missing_self_paths']:
                print("MISSING SELF-PATHS (no depth=0 entry):")
                for item in issues['missing_self_paths']:
                    print(f"  - {item['id']}: {item['title']}")
                print()

            if issues['parent_mismatch']:
                print("PARENT MISMATCH (ID doesn't match actual parent):")
                for item in issues['parent_mismatch']:
                    print(f"  - {item['id']}: actual={item['actual_parent']}, expected={item['expected_parent']}")
                print()

            if issues['invalid_id_format']:
                print("INVALID ID FORMAT:")
                for item in issues['invalid_id_format']:
                    print(f"  - {item['id']}: {item['reason']}")
                print()

    return 0 if total_issues == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
