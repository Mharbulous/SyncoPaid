#!/usr/bin/env python
"""Story vetting conflict classification cache.

Provides persistent caching for LLM classification decisions to avoid
repeatedly analyzing the same story pairs. Uses version tracking to
invalidate cache entries when stories change.

References:
- Entity Resolution / Record Linkage pattern
- Incremental Linkage for avoiding O(N^2) re-comparisons
"""

import sqlite3
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import (
    DB_PATH,
    CLASSIFICATIONS,
    ACTIONS,
    make_pair_key,
    get_story_version,
)


def migrate_schema(conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Add version column and vetting_decisions table.

    Safe to run multiple times - checks for existing schema.

    Returns:
        Dict with migration results: {'version_added': bool, 'table_created': bool}
    """
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        should_close = True

    result = {'version_added': False, 'table_created': False}

    try:
        cursor = conn.cursor()

        # Check if version column exists
        cursor.execute("PRAGMA table_info(story_nodes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'version' not in columns:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN version INTEGER DEFAULT 1")
            result['version_added'] = True

        # Check if vetting_decisions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='vetting_decisions'
        """)
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            cursor.execute('''
                CREATE TABLE vetting_decisions (
                    pair_key TEXT PRIMARY KEY,
                    story_a_id TEXT NOT NULL,
                    story_a_version INTEGER NOT NULL,
                    story_b_id TEXT NOT NULL,
                    story_b_version INTEGER NOT NULL,
                    classification TEXT NOT NULL CHECK (classification IN (
                        'duplicate', 'scope_overlap', 'competing',
                        'incompatible', 'false_positive'
                    )),
                    action_taken TEXT CHECK (action_taken IN (
                        'SKIP', 'DELETE_CONCEPT', 'REJECT_CONCEPT', 'DUPLICATIVE_CONCEPT',
                        'BLOCK_CONCEPT', 'TRUE_MERGE', 'PICK_BETTER', 'HUMAN_REVIEW', 'DEFER_PENDING'
                    )),
                    decided_at TEXT NOT NULL,
                    FOREIGN KEY (story_a_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (story_b_id) REFERENCES story_nodes(id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for fast lookups
            cursor.execute('CREATE INDEX idx_vetting_story_a ON vetting_decisions(story_a_id)')
            cursor.execute('CREATE INDEX idx_vetting_story_b ON vetting_decisions(story_b_id)')
            result['table_created'] = True

        conn.commit()

    finally:
        if should_close:
            conn.close()

    return result


def get_cached_decision(conn: sqlite3.Connection, id_a: str, id_b: str) -> Optional[Dict[str, Any]]:
    """Look up cached decision for a pair.

    Returns None if not cached or if versions don't match (invalidated).
    Automatically cleans up entries for deleted stories.

    Args:
        conn: SQLite connection
        id_a: First story ID
        id_b: Second story ID

    Returns:
        Dict with classification and action_taken, or None if cache miss/stale
    """
    pair_key = make_pair_key(id_a, id_b)

    # Get cached decision
    cached = conn.execute('''
        SELECT story_a_id, story_a_version, story_b_id, story_b_version,
               classification, action_taken
        FROM vetting_decisions
        WHERE pair_key = ?
    ''', (pair_key,)).fetchone()

    if not cached:
        return None

    story_a_id, story_a_ver, story_b_id, story_b_ver, classification, action_taken = cached

    # Get current versions
    current_versions = {}
    for story_id in (story_a_id, story_b_id):
        row = conn.execute(
            'SELECT version FROM story_nodes WHERE id = ?', (story_id,)
        ).fetchone()
        if row is None:
            # Story was deleted - invalidate cache entry
            conn.execute('DELETE FROM vetting_decisions WHERE pair_key = ?', (pair_key,))
            conn.commit()
            return None
        current_versions[story_id] = row[0] or 1

    # Check if versions match
    if (current_versions[story_a_id] != story_a_ver or
        current_versions[story_b_id] != story_b_ver):
        # Versions changed - cache is stale
        return None

    return {
        'pair_key': pair_key,
        'classification': classification,
        'action_taken': action_taken,
        'valid': True
    }


def store_decision(conn: sqlite3.Connection, id_a: str, id_b: str,
                   classification: str, action_taken: str) -> None:
    """Store classification decision in cache.

    Args:
        conn: SQLite connection
        id_a: First story ID
        id_b: Second story ID
        classification: One of CLASSIFICATIONS
        action_taken: One of ACTIONS
    """
    pair_key = make_pair_key(id_a, id_b)

    # Get current versions using common utility
    ver_a = get_story_version(conn, id_a)
    ver_b = get_story_version(conn, id_b)

    # Ensure canonical ordering in storage (smaller ID first)
    if id_a < id_b:
        story_a_id, story_a_ver = id_a, ver_a
        story_b_id, story_b_ver = id_b, ver_b
    else:
        story_a_id, story_a_ver = id_b, ver_b
        story_b_id, story_b_ver = id_a, ver_a

    conn.execute('''
        INSERT OR REPLACE INTO vetting_decisions
        (pair_key, story_a_id, story_a_version, story_b_id, story_b_version,
         classification, action_taken, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pair_key, story_a_id, story_a_ver, story_b_id, story_b_ver,
        classification, action_taken, datetime.now().isoformat()
    ))
    conn.commit()


def invalidate_story_cache(conn: sqlite3.Connection, story_id: str) -> int:
    """Invalidate all cached decisions involving a story.

    Call this when a story is deleted or significantly modified.

    Returns:
        Number of cache entries deleted
    """
    cursor = conn.execute('''
        DELETE FROM vetting_decisions
        WHERE story_a_id = ? OR story_b_id = ?
    ''', (story_id, story_id))
    conn.commit()
    return cursor.rowcount


def get_cache_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get statistics about the vetting cache.

    Returns:
        Dict with cache statistics
    """
    total = conn.execute('SELECT COUNT(*) FROM vetting_decisions').fetchone()[0]

    by_classification = {}
    for row in conn.execute('''
        SELECT classification, COUNT(*)
        FROM vetting_decisions
        GROUP BY classification
    ''').fetchall():
        by_classification[row[0]] = row[1]

    by_action = {}
    for row in conn.execute('''
        SELECT action_taken, COUNT(*)
        FROM vetting_decisions
        GROUP BY action_taken
    ''').fetchall():
        by_action[row[0]] = row[1]

    return {
        'total_cached': total,
        'by_classification': by_classification,
        'by_action': by_action
    }


def clear_cache(conn: sqlite3.Connection) -> int:
    """Clear all cached decisions.

    Returns:
        Number of entries deleted
    """
    cursor = conn.execute('DELETE FROM vetting_decisions')
    conn.commit()
    return cursor.rowcount


# CLI for testing
if __name__ == '__main__':
    import sys

    conn = sqlite3.connect(DB_PATH)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'migrate':
            result = migrate_schema(conn)
            print(f"Migration result: {result}")

        elif cmd == 'stats':
            stats = get_cache_stats(conn)
            print(f"Cache statistics:")
            print(f"  Total cached: {stats['total_cached']}")
            print(f"  By classification: {stats['by_classification']}")
            print(f"  By action: {stats['by_action']}")

        elif cmd == 'clear':
            count = clear_cache(conn)
            print(f"Cleared {count} cached decisions")

        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python vetting_cache.py [migrate|stats|clear]")
    else:
        print("Usage: python vetting_cache.py [migrate|stats|clear]")

    conn.close()
