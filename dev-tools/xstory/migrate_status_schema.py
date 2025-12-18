#!/usr/bin/env python3
"""
Migrate story-tree.db to use the updated 21-status schema.

This script:
1. Creates a backup of the existing database
2. Creates a new database with the updated schema
3. Migrates all data, mapping old statuses to new ones
4. Replaces the old database with the new one

Status mappings:
- bugged -> broken
- in-progress -> active
- epic -> concept (demoted - needs re-approval)
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Paths
DB_PATH = Path(__file__).parent.parent.parent / '.claude' / 'data' / 'story-tree.db'
BACKUP_PATH = DB_PATH.with_suffix('.db.backup')
TEMP_PATH = DB_PATH.with_suffix('.db.new')

# Status mapping from old to new
STATUS_MAPPING = {
    'bugged': 'broken',
    'in-progress': 'active',
    'epic': 'concept',  # Demote epics to concepts for re-evaluation
}

# New schema with 21 statuses
NEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN (
            'infeasible', 'rejected', 'wishlist',
            'concept', 'broken', 'blocked', 'refine',
            'pending', 'approved', 'planned', 'pending', 'paused',
            'active',
            'reviewing', 'implemented',
            'ready', 'polish', 'released',
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


def migrate():
    """Run the migration."""
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    print(f"Migrating: {DB_PATH}")
    print(f"Backup to: {BACKUP_PATH}")

    # Step 1: Create backup
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("[OK] Backup created")

    # Step 2: Connect to old database
    old_conn = sqlite3.connect(DB_PATH)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    # Step 3: Create new database with updated schema
    if TEMP_PATH.exists():
        TEMP_PATH.unlink()
    new_conn = sqlite3.connect(TEMP_PATH)
    new_cursor = new_conn.cursor()
    new_cursor.executescript(NEW_SCHEMA)
    print("[OK] New schema created")

    # Step 4: Migrate story_nodes
    old_cursor.execute("SELECT * FROM story_nodes")
    nodes = old_cursor.fetchall()

    migrated_statuses = {}
    for node in nodes:
        old_status = node['status']
        new_status = STATUS_MAPPING.get(old_status, old_status)

        if old_status != new_status:
            migrated_statuses[old_status] = migrated_statuses.get(old_status, 0) + 1

        new_cursor.execute("""
            INSERT INTO story_nodes
            (id, title, description, capacity, status, project_path,
             last_implemented, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node['id'], node['title'], node['description'], node['capacity'],
            new_status, node['project_path'], node['last_implemented'],
            node['notes'], node['created_at'], node['updated_at']
        ))

    print(f"[OK] Migrated {len(nodes)} nodes")
    if migrated_statuses:
        print("    Status changes:")
        for old, count in migrated_statuses.items():
            print(f"      {old} -> {STATUS_MAPPING[old]}: {count} nodes")

    # Step 5: Migrate story_paths
    old_cursor.execute("SELECT * FROM story_paths")
    paths = old_cursor.fetchall()

    for path in paths:
        new_cursor.execute("""
            INSERT INTO story_paths (ancestor_id, descendant_id, depth)
            VALUES (?, ?, ?)
        """, (path['ancestor_id'], path['descendant_id'], path['depth']))

    print(f"[OK] Migrated {len(paths)} paths")

    # Step 6: Migrate story_commits (if table exists)
    old_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='story_commits'"
    )
    if old_cursor.fetchone():
        old_cursor.execute("SELECT * FROM story_commits")
        commits = old_cursor.fetchall()

        for commit in commits:
            new_cursor.execute("""
                INSERT INTO story_commits (story_id, commit_hash, commit_date, commit_message)
                VALUES (?, ?, ?, ?)
            """, (commit['story_id'], commit['commit_hash'],
                  commit['commit_date'], commit['commit_message']))

        print(f"[OK] Migrated {len(commits)} commits")
    else:
        print("[OK] No story_commits table to migrate (table will be created empty)")

    # Step 7: Migrate metadata and update version
    old_cursor.execute("SELECT * FROM metadata")
    metadata = old_cursor.fetchall()

    for meta in metadata:
        if meta['key'] == 'version':
            new_cursor.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                ('version', '3.0.0')
            )
        else:
            new_cursor.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                (meta['key'], meta['value'])
            )

    # Add migration timestamp
    new_cursor.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
        ('lastMigration', datetime.now().isoformat())
    )

    print("[OK] Migrated metadata, updated version to 3.0.0")

    # Step 8: Commit and close
    new_conn.commit()
    old_conn.close()
    new_conn.close()

    # Step 9: Replace old database with new
    DB_PATH.unlink()
    TEMP_PATH.rename(DB_PATH)

    print(f"\n[SUCCESS] Migration complete!")
    print(f"  Old database backed up to: {BACKUP_PATH}")
    print(f"  New database at: {DB_PATH}")

    return True


def verify():
    """Verify the migration was successful."""
    print("\nVerifying migration...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='story_nodes'")
    schema = cursor.fetchone()[0]

    if 'broken' in schema and 'bugged' not in schema:
        print("[OK] Schema updated correctly")
    else:
        print("[WARN] Schema may not be fully updated")

    # Check for any invalid statuses
    cursor.execute("""
        SELECT status, COUNT(*) FROM story_nodes
        WHERE status NOT IN (
            'infeasible', 'rejected', 'wishlist',
            'concept', 'broken', 'blocked', 'refine',
            'pending', 'approved', 'planned', 'pending', 'paused',
            'active',
            'reviewing', 'implemented',
            'ready', 'polish', 'released',
            'legacy', 'deprecated', 'archived'
        )
        GROUP BY status
    """)
    invalid = cursor.fetchall()

    if invalid:
        print("[ERROR] Found invalid statuses:")
        for status, count in invalid:
            print(f"  {status}: {count}")
    else:
        print("[OK] All statuses are valid")

    # Show status distribution
    cursor.execute("SELECT status, COUNT(*) FROM story_nodes GROUP BY status ORDER BY COUNT(*) DESC")
    print("\nCurrent status distribution:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")

    conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify()
    else:
        if migrate():
            verify()
