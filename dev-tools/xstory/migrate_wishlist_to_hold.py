#!/usr/bin/env python3
"""
Migrate wishlist from disposition to hold_reason.

This script migrates existing 'wishlist' values from the disposition field
to the hold_reason field, reflecting the semantic change that wishlist is
an indefinite hold (can be revived) rather than a terminal state.

Migration:
1. Recreates story_nodes table with updated CHECK constraints
2. For rows where disposition = 'wishlist':
   - Set hold_reason = 'wishlist'
   - Set disposition = NULL

Usage:
    python migrate_wishlist_to_hold.py [--db PATH] [--dry-run]
"""

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


# New schema with wishlist in hold_reason instead of disposition
NEW_TABLE_SCHEMA = """
CREATE TABLE story_nodes_new (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,
    stage TEXT NOT NULL DEFAULT 'concept'
        CHECK (stage IN (
            'concept', 'approved', 'planned', 'active',
            'reviewing', 'verifying', 'implemented', 'ready', 'polish', 'released'
        )),
    hold_reason TEXT DEFAULT NULL
        CHECK (hold_reason IS NULL OR hold_reason IN (
            'queued', 'pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist'
        )),
    disposition TEXT DEFAULT NULL
        CHECK (disposition IS NULL OR disposition IN (
            'rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived'
        )),
    human_review INTEGER DEFAULT 0
        CHECK (human_review IN (0, 1)),
    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    version INTEGER DEFAULT 1
);
"""


def find_default_db() -> Path:
    """Find the default database path."""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / '.claude' / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path
    cwd = Path.cwd()
    for check in [cwd, cwd.parent, cwd.parent.parent]:
        candidate = check / '.claude' / 'data' / 'story-tree.db'
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find story-tree.db")


def migrate(db_path: Path, dry_run: bool = False) -> dict:
    """
    Migrate wishlist from disposition to hold_reason.

    This involves:
    1. Creating a new table with updated CHECK constraints
    2. Copying all data, converting wishlist disposition to hold_reason
    3. Replacing the old table with the new one

    Returns:
        dict with migration statistics
    """
    stats = {
        'total_wishlist': 0,
        'migrated': 0,
        'skipped_has_hold': 0,
        'backup_path': None,
        'schema_updated': False,
    }

    # Create backup
    if not dry_run:
        backup_path = db_path.with_suffix(f'.db.backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(db_path, backup_path)
        stats['backup_path'] = str(backup_path)
        print(f"Created backup: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all wishlist items first (for reporting)
    cursor.execute("""
        SELECT id, title, stage, hold_reason, disposition
        FROM story_nodes
        WHERE disposition = 'wishlist'
    """)
    wishlist_rows = cursor.fetchall()
    stats['total_wishlist'] = len(wishlist_rows)

    print(f"\nFound {len(wishlist_rows)} stories with disposition='wishlist'")
    for row in wishlist_rows:
        if row['hold_reason']:
            print(f"  SKIP: {row['id']} - already has hold_reason='{row['hold_reason']}'")
            stats['skipped_has_hold'] += 1
        else:
            print(f"  {'[DRY RUN] Would migrate' if dry_run else 'Will migrate'}: {row['id']} - {row['title'][:50]}")
            stats['migrated'] += 1

    if dry_run:
        conn.close()
        return stats

    # Step 1: Create new table with updated schema
    print("\nStep 1: Creating new table with updated CHECK constraints...")
    cursor.execute("DROP TABLE IF EXISTS story_nodes_new")
    cursor.executescript(NEW_TABLE_SCHEMA)

    # Step 2: Copy all data, converting wishlist disposition to hold_reason
    print("Step 2: Copying data with wishlist migration...")
    cursor.execute("""
        INSERT INTO story_nodes_new (
            id, title, description, capacity, stage,
            hold_reason, disposition, human_review,
            project_path, last_implemented, notes,
            created_at, updated_at, version
        )
        SELECT
            id, title, description, capacity, stage,
            CASE
                WHEN disposition = 'wishlist' AND hold_reason IS NULL THEN 'wishlist'
                ELSE hold_reason
            END as hold_reason,
            CASE
                WHEN disposition = 'wishlist' THEN NULL
                ELSE disposition
            END as disposition,
            human_review,
            project_path, last_implemented, notes,
            created_at, datetime('now'), version
        FROM story_nodes
    """)

    # Step 3: Drop old table and rename new
    print("Step 3: Replacing old table with new...")
    cursor.execute("DROP TABLE story_nodes")
    cursor.execute("ALTER TABLE story_nodes_new RENAME TO story_nodes")

    # Step 4: Recreate indexes
    print("Step 4: Recreating indexes...")
    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_active_pipeline ON story_nodes(stage)
            WHERE disposition IS NULL AND hold_reason IS NULL;
        CREATE INDEX IF NOT EXISTS idx_held_stories ON story_nodes(hold_reason)
            WHERE hold_reason IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_disposed_stories ON story_nodes(disposition)
            WHERE disposition IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_needs_review ON story_nodes(human_review)
            WHERE human_review = 1;
    """)

    # Step 5: Recreate trigger
    print("Step 5: Recreating trigger...")
    cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
        AFTER UPDATE ON story_nodes
        FOR EACH ROW
        BEGIN
            UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
        END;
    """)

    conn.commit()
    stats['schema_updated'] = True
    print("Step 6: Committed changes.")

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Migrate wishlist from disposition to hold_reason'
    )
    parser.add_argument(
        '--db', type=Path, default=None,
        help='Path to story-tree.db (auto-detected if not specified)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would be changed without making changes'
    )

    args = parser.parse_args()

    try:
        db_path = args.db or find_default_db()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    print(f"Database: {db_path}")
    if args.dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    else:
        print("Mode: LIVE (changes will be committed)")

    stats = migrate(db_path, dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print("Migration Summary")
    print("=" * 50)
    print(f"Total wishlist items found: {stats['total_wishlist']}")
    print(f"Migrated: {stats['migrated']}")
    print(f"Skipped (already has hold_reason): {stats['skipped_has_hold']}")
    if stats.get('schema_updated'):
        print("Schema updated: Yes (CHECK constraints modified)")
    if stats['backup_path']:
        print(f"Backup created: {stats['backup_path']}")

    if args.dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to apply.")
    else:
        print("\nMigration complete!")

    return 0


if __name__ == '__main__':
    exit(main())
