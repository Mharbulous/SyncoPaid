#!/usr/bin/env python3
"""
Story Tree Migration: v2.x → v3.0 (21-Status System)

Usage: python migrate_v1_to_v2.py [--db PATH] [--no-backup] [--dry-run] [--force]
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

NEW_VERSION = "3.0.0"

OLD_STATUSES = [
    'concept', 'approved', 'epic', 'rejected', 'wishlist', 'planned',
    'queued', 'active', 'in-progress', 'bugged', 'implemented', 'ready',
    'deprecated', 'infeasible'
]

NEW_STATUSES = [
    'infeasible', 'rejected', 'wishlist',
    'concept', 'broken', 'blocked', 'refine',
    'deferred', 'approved', 'planned', 'queued', 'paused',
    'active',
    'reviewing', 'implemented',
    'ready', 'polish', 'released',
    'legacy', 'deprecated', 'archived',
]


def find_default_db() -> Path:
    cwd = Path.cwd()
    db_path = cwd / '.claude' / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path
    raise FileNotFoundError("Could not find story-tree.db. Use --db to specify the path.")


def get_current_version(conn: sqlite3.Connection) -> str:
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'version'")
        row = cursor.fetchone()
        return row[0] if row else "unknown"
    except sqlite3.Error:
        return "unknown"


def backup_database(db_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"story-tree-backup-{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def validate_existing_data(conn: sqlite3.Connection) -> tuple[bool, list[str]]:
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT status FROM story_nodes")
    existing_statuses = {row[0] for row in cursor.fetchall()}
    invalid = existing_statuses - set(OLD_STATUSES) - set(NEW_STATUSES)
    return (True, []) if not invalid else (False, list(invalid))


def get_commits_table_name(conn: sqlite3.Connection) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%commit%'")
    row = cursor.fetchone()
    return row[0] if row else None


def migrate_database(db_path: Path, dry_run: bool = False) -> bool:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story_nodes")
        total_nodes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM story_paths")
        total_paths = cursor.fetchone()[0]

        print(f"Nodes: {total_nodes}, Paths: {total_paths}")

        if dry_run:
            print("[DRY RUN] No changes made.")
            conn.close()
            return True

        cursor.execute("BEGIN TRANSACTION")

        # Create new table with updated status constraint
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

        cursor.execute("""
            INSERT INTO story_nodes_new (id, title, description, capacity, status,
                                        project_path, last_implemented, notes,
                                        created_at, updated_at)
            SELECT id, title, COALESCE(description, ''), capacity, status,
                   project_path, last_implemented, notes,
                   COALESCE(created_at, datetime('now')),
                   COALESCE(updated_at, datetime('now'))
            FROM story_nodes
        """)

        cursor.execute("DROP TABLE story_nodes")
        cursor.execute("ALTER TABLE story_nodes_new RENAME TO story_nodes")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status)")

        cursor.execute("DROP TRIGGER IF EXISTS story_nodes_updated_at")
        cursor.execute("""
            CREATE TRIGGER story_nodes_updated_at
            AFTER UPDATE ON story_nodes FOR EACH ROW
            BEGIN
                UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('version', ?)", (NEW_VERSION,))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastMigration', ?)",
                      (f"v2.x to v3.0.0 on {datetime.now().isoformat()}",))

        conn.commit()
        print(f"Migration complete! Version: {NEW_VERSION}")
        conn.close()
        return True

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"Migration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate story-tree database v2.x → v3.0')
    parser.add_argument('--db', type=Path, help='Database path')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--force', action='store_true', help='Force migration even if at v3.0')
    args = parser.parse_args()

    try:
        db_path = args.db if args.db else find_default_db()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    print(f"Database: {db_path}")
    conn = sqlite3.connect(db_path)
    current_version = get_current_version(conn)
    print(f"Current version: {current_version}")

    if current_version.startswith("3.") and not args.force:
        print(f"Already at version {current_version}. Use --force to re-run.")
        conn.close()
        sys.exit(0)

    valid, invalid_statuses = validate_existing_data(conn)
    conn.close()

    if not valid:
        print(f"Invalid statuses: {invalid_statuses}")
        sys.exit(1)

    if not args.no_backup and not args.dry_run:
        backup_path = backup_database(db_path)
        print(f"Backup: {backup_path}")

    success = migrate_database(db_path, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
