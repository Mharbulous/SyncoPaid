#!/usr/bin/env python3
"""
Story Tree Migration Script: v2.x → v3.0 (21-Status System)

Migrates existing story-tree database from the 14-status system to the new
21-status rainbow system. All existing statuses map directly (no changes needed).

New statuses not in v1:
- refine, blocked, broken, deferred, paused, reviewing, polish, released, legacy, archived

Usage:
    python migrate_v1_to_v2.py [OPTIONS]

Options:
    --db PATH           Path to database (default: .claude/data/story-tree.db)
    --backup            Create backup before migration (default: True)
    --no-backup         Skip backup creation
    --dry-run           Show what would be done without making changes
    --force             Force migration even if already at v3.0
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Version info
OLD_VERSION_PREFIX = "2."
NEW_VERSION = "3.0.0"

# Old statuses (v2.x - 14 statuses)
OLD_STATUSES = [
    'concept', 'approved', 'epic', 'rejected', 'wishlist', 'planned',
    'queued', 'active', 'in-progress', 'bugged', 'implemented', 'ready',
    'deprecated', 'infeasible'
]

# New statuses (v3.0 - 21 statuses - canonical order)
NEW_STATUSES = [
    # Red Zone (Can't/Won't)
    'infeasible', 'rejected', 'wishlist',
    # Orange-Yellow Zone (Concept & Broken)
    'concept', 'broken', 'blocked', 'refine',
    # Yellow Zone (Planning)
    'deferred', 'approved', 'planned', 'queued', 'paused',
    # Green Zone (Development)
    'active',
    # Cyan-Blue Zone (Testing)
    'reviewing', 'implemented',
    # Blue Zone (Production)
    'ready', 'polish', 'released',
    # Violet Zone (Post-Production/End-of-Life)
    'legacy', 'deprecated', 'archived',
]

# New schema with 21 statuses
NEW_SCHEMA = """
-- Story Tree SQLite Schema
-- Version: 3.0.0
-- Pattern: Closure table for hierarchical data
-- Location: .claude/data/story-tree.db

--------------------------------------------------------------------------------
-- STORY_NODES: Main table storing all story data
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN (
            -- Red Zone (Can't/Won't)
            'infeasible', 'rejected', 'wishlist',
            -- Orange-Yellow Zone (Concept & Broken)
            'concept', 'broken', 'blocked', 'refine',
            -- Yellow Zone (Planning)
            'deferred', 'approved', 'planned', 'queued', 'paused',
            -- Green Zone (Development)
            'active',
            -- Cyan-Blue Zone (Testing)
            'reviewing', 'implemented',
            -- Blue Zone (Production)
            'ready', 'polish', 'released',
            -- Violet Zone (Post-Production/End-of-Life)
            'legacy', 'deprecated', 'archived'
        )),
    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);

CREATE TABLE IF NOT EXISTS story_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);

CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;
"""


def find_default_db() -> Path:
    """Find the default story-tree database location."""
    # Try current working directory structure
    cwd = Path.cwd()
    db_path = cwd / '.claude' / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path

    # Try relative to script
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path

    raise FileNotFoundError(
        "Could not find story-tree.db. Use --db to specify the path."
    )


def get_current_version(conn: sqlite3.Connection) -> str:
    """Get the current schema version from metadata."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'version'")
        row = cursor.fetchone()
        return row[0] if row else "unknown"
    except sqlite3.Error:
        return "unknown"


def backup_database(db_path: Path) -> Path:
    """Create a timestamped backup of the database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"story-tree-backup-{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def validate_existing_data(conn: sqlite3.Connection) -> tuple[bool, list[str]]:
    """Validate that all existing statuses are valid for migration."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT status FROM story_nodes")
    existing_statuses = {row[0] for row in cursor.fetchall()}

    # Check for any invalid statuses
    invalid = existing_statuses - set(OLD_STATUSES) - set(NEW_STATUSES)
    if invalid:
        return False, list(invalid)
    return True, []


def get_commits_table_name(conn: sqlite3.Connection) -> str:
    """Determine the name of the commits table (may vary between versions)."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%commit%'")
    row = cursor.fetchone()
    return row[0] if row else None


def get_migration_stats(conn: sqlite3.Connection) -> dict:
    """Get statistics about the data to be migrated."""
    cursor = conn.cursor()

    # Count nodes by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM story_nodes
        GROUP BY status
        ORDER BY count DESC
    """)
    status_counts = dict(cursor.fetchall())

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM story_nodes")
    total_nodes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM story_paths")
    total_paths = cursor.fetchone()[0]

    # Handle different commit table names
    commits_table = get_commits_table_name(conn)
    if commits_table:
        cursor.execute(f"SELECT COUNT(*) FROM {commits_table}")
        total_commits = cursor.fetchone()[0]
    else:
        total_commits = 0

    return {
        'total_nodes': total_nodes,
        'total_paths': total_paths,
        'total_commits': total_commits,
        'commits_table': commits_table,
        'status_counts': status_counts,
    }


def migrate_database(db_path: Path, dry_run: bool = False) -> bool:
    """
    Perform the migration from v2.x to v3.0.

    Since SQLite doesn't support modifying CHECK constraints, we need to:
    1. Create new tables with updated schema
    2. Copy all data from old tables
    3. Drop old tables
    4. Rename new tables
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Get stats before migration
        stats = get_migration_stats(conn)
        commits_table = stats.get('commits_table')

        print(f"\nMigration Statistics:")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Total paths: {stats['total_paths']}")
        print(f"  Total commits: {stats['total_commits']}")
        if commits_table:
            print(f"  Commits table: {commits_table}")
        print(f"\n  Status distribution:")
        for status, count in stats['status_counts'].items():
            print(f"    {status}: {count}")

        if dry_run:
            print("\n[DRY RUN] No changes made.")
            conn.close()
            return True

        cursor = conn.cursor()

        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create new tables with updated schema (with _new suffix)
        cursor.execute("""
            CREATE TABLE story_nodes_new (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                capacity INTEGER,
                status TEXT NOT NULL DEFAULT 'concept'
                    CHECK (status IN (
                        'infeasible', 'rejected', 'wishlist',
                        'concept', 'refine', 'approved', 'epic',
                        'planned', 'blocked', 'deferred',
                        'queued', 'bugged', 'paused',
                        'active', 'in-progress',
                        'reviewing', 'implemented',
                        'ready', 'polish', 'released',
                        'legacy', 'deprecated', 'archived'
                    )),
                project_path TEXT,
                last_implemented TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Copy data from old table to new table
        # Use COALESCE to handle any NULL values in required fields
        cursor.execute("""
            INSERT INTO story_nodes_new (id, title, description, capacity, status,
                                        project_path, last_implemented, notes,
                                        created_at, updated_at)
            SELECT id, title,
                   COALESCE(description, ''),
                   capacity, status, project_path, last_implemented, notes,
                   COALESCE(created_at, datetime('now')),
                   COALESCE(updated_at, datetime('now'))
            FROM story_nodes
        """)

        # Drop old table and rename new one
        cursor.execute("DROP TABLE story_nodes")
        cursor.execute("ALTER TABLE story_nodes_new RENAME TO story_nodes")

        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status)")

        # Recreate trigger
        cursor.execute("DROP TRIGGER IF EXISTS story_nodes_updated_at")
        cursor.execute("""
            CREATE TRIGGER story_nodes_updated_at
            AFTER UPDATE ON story_nodes
            FOR EACH ROW
            BEGIN
                UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        # Update version in metadata
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES ('version', ?)
        """, (NEW_VERSION,))

        # Add migration note
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES ('lastMigration', ?)
        """, (f"v2.x to v3.0.0 on {datetime.now().isoformat()}",))

        # Commit transaction
        conn.commit()

        # Verify migration
        new_version = get_current_version(conn)
        post_stats = get_migration_stats(conn)

        print(f"\n✓ Migration complete!")
        print(f"  Version: {new_version}")
        print(f"  Nodes preserved: {post_stats['total_nodes']}")
        print(f"  Paths preserved: {post_stats['total_paths']}")
        print(f"  Commits preserved: {post_stats['total_commits']}")

        conn.close()
        return True

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"\n✗ Migration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Migrate story-tree database from v2.x to v3.0 (23-status system)'
    )
    parser.add_argument(
        '--db',
        type=Path,
        help='Path to database (default: .claude/data/story-tree.db)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Create backup before migration (default: True)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if already at v3.0'
    )

    args = parser.parse_args()

    # Find database
    try:
        db_path = args.db if args.db else find_default_db()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    print(f"Story Tree Migration: v2.x → v3.0 (23-Status System)")
    print(f"=" * 50)
    print(f"Database: {db_path}")

    # Connect and check version
    conn = sqlite3.connect(db_path)
    current_version = get_current_version(conn)
    print(f"Current version: {current_version}")

    # Check if already migrated
    if current_version.startswith("3.") and not args.force:
        print(f"\n✓ Database is already at version {current_version}")
        print("  Use --force to re-run migration")
        conn.close()
        sys.exit(0)

    # Validate data
    valid, invalid_statuses = validate_existing_data(conn)
    conn.close()

    if not valid:
        print(f"\n✗ Invalid statuses found: {invalid_statuses}")
        print("  Please fix these statuses before migration")
        sys.exit(1)

    # Create backup unless --no-backup
    if args.backup and not args.no_backup and not args.dry_run:
        backup_path = backup_database(db_path)
        print(f"Backup created: {backup_path}")

    # Run migration
    success = migrate_database(db_path, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
