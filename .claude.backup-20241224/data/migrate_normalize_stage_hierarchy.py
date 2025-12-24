#!/usr/bin/env python3
"""
Migration: Normalize Stage Hierarchy

Enforces the multi-faceted stage rule from workflow-diagrams.md (lines 86-101):
"A node cannot reach implemented until both its own work is complete AND
all children have reached implemented or later."

This migration demotes parent nodes at 'implemented' or later stages back to
'active' if they have children that haven't reached 'implemented' yet.

Usage: python -m .claude.data.migrate_normalize_stage_hierarchy
"""
import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = '.claude/data/story-tree.db'

# Stages considered "complete" (implemented or later)
FINAL_STAGES = ('implemented', 'ready', 'polish', 'released')

# Target stage for demotion (work still in progress)
DEMOTE_TO_STAGE = 'active'


def get_violations(cursor):
    """
    Find nodes violating the multi-faceted stage rule:
    - Parent at implemented or later stage
    - Has at least one child NOT at implemented or later
    - Excludes disposed children (they've exited the pipeline)
    """
    cursor.execute('''
        SELECT
            parent.id,
            parent.title,
            parent.stage,
            COUNT(child.id) as total_children,
            SUM(CASE WHEN child.stage NOT IN (?, ?, ?, ?) THEN 1 ELSE 0 END) as non_impl_children
        FROM story_nodes parent
        JOIN story_paths sp ON sp.ancestor_id = parent.id AND sp.depth = 1
        JOIN story_nodes child ON child.id = sp.descendant_id
        WHERE parent.stage IN (?, ?, ?, ?)
          AND child.disposition IS NULL
        GROUP BY parent.id
        HAVING non_impl_children > 0
        ORDER BY parent.id
    ''', (*FINAL_STAGES, *FINAL_STAGES))

    return cursor.fetchall()


def demote_node(cursor, node_id, old_stage):
    """Demote a single node to active stage."""
    cursor.execute('''
        UPDATE story_nodes
        SET stage = ?, updated_at = datetime('now')
        WHERE id = ?
    ''', (DEMOTE_TO_STAGE, node_id))
    return cursor.rowcount


def main():
    if not os.path.exists(DB_PATH):
        print(f'[ERROR] Database not found: {DB_PATH}')
        return 1

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print('=' * 70)
    print('Migration: Normalize Stage Hierarchy')
    print(f'Database: {DB_PATH}')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print('=' * 70)
    print()

    # Find violations
    violations = get_violations(cursor)

    if not violations:
        print('[OK] No violations found. Database is already normalized.')
        conn.close()
        return 0

    print(f'Found {len(violations)} node(s) violating multi-faceted stage rule:')
    print()
    print(f'{"ID":<12} {"Title":<35} {"Stage":<12} {"Children":<10} {"Non-Impl":<10}')
    print('-' * 70)

    for row in violations:
        node_id, title, stage, total_children, non_impl_children = row
        print(f'{node_id:<12} {title[:35]:<35} {stage:<12} {total_children:<10} {non_impl_children:<10}')

    print()
    print(f'Demoting all {len(violations)} nodes to stage: {DEMOTE_TO_STAGE}')
    print()

    # Apply demotions
    changes = []
    for row in violations:
        node_id, title, old_stage, total_children, non_impl_children = row
        demote_node(cursor, node_id, old_stage)
        changes.append({
            'id': node_id,
            'title': title,
            'old_stage': old_stage,
            'new_stage': DEMOTE_TO_STAGE,
            'non_impl_children': non_impl_children
        })
        print(f'  [DEMOTED] {node_id}: {old_stage} -> {DEMOTE_TO_STAGE}')

    # Commit changes
    conn.commit()

    print()
    print('=' * 70)
    print('AUDIT LOG')
    print('=' * 70)
    for change in changes:
        print(f"  {change['id']}: {change['old_stage']} -> {change['new_stage']} "
              f"(had {change['non_impl_children']} incomplete children)")

    print()
    print(f'[OK] Migration complete. {len(changes)} node(s) updated.')

    # Verify no violations remain
    remaining = get_violations(cursor)
    if remaining:
        print(f'[WARNING] {len(remaining)} violations still remain after migration!')
        conn.close()
        return 1
    else:
        print('[OK] Verification passed. No violations remain.')

    conn.close()
    return 0


if __name__ == '__main__':
    exit(main())
