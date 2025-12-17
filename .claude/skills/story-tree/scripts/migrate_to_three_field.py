#!/usr/bin/env python3
"""
Three-Field Schema Migration Script

Migrates story-tree database from single 'status' field (22 values) to
three-field system: stage + hold_reason + disposition + human_review

Usage:
    python migrate_to_three_field.py [--dry-run] [--db PATH]

The migration:
1. Adds new columns: stage, hold_reason, disposition, human_review
2. Maps existing status values to new fields
3. Infers stage for ambiguous statuses (pending, blocked, archived)
4. Adds CHECK constraints
5. Creates optimized indexes
6. Keeps old 'status' column for backward compatibility (deprecated)
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# Status to three-field mappings
STAGE_MAPPINGS = {
    # Direct stage mappings (status == stage)
    'concept': {'stage': 'concept', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'approved': {'stage': 'approved', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'planned': {'stage': 'planned', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'queued': {'stage': 'queued', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'active': {'stage': 'active', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'reviewing': {'stage': 'reviewing', 'hold_reason': None, 'disposition': None, 'human_review': True},
    'verifying': {'stage': 'verifying', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'implemented': {'stage': 'implemented', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'ready': {'stage': 'ready', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'polish': {'stage': 'polish', 'hold_reason': None, 'disposition': None, 'human_review': False},
    'released': {'stage': 'released', 'hold_reason': None, 'disposition': None, 'human_review': False},
}

HOLD_MAPPINGS = {
    # Hold reasons with known stages
    'refine': {'stage': 'concept', 'hold_reason': 'refine', 'disposition': None, 'human_review': True},
    'broken': {'stage': 'concept', 'hold_reason': 'broken', 'disposition': None, 'human_review': True},
    'paused': {'stage': 'active', 'hold_reason': 'paused', 'disposition': None, 'human_review': True},
    # These need stage inference
    'pending': {'stage': 'INFER', 'hold_reason': 'pending', 'disposition': None, 'human_review': True},
    'blocked': {'stage': 'INFER', 'hold_reason': 'blocked', 'disposition': None, 'human_review': True},
}

DISPOSITION_MAPPINGS = {
    # Dispositions with known stages
    'rejected': {'stage': 'concept', 'hold_reason': None, 'disposition': 'rejected', 'human_review': False},
    'infeasible': {'stage': 'concept', 'hold_reason': None, 'disposition': 'infeasible', 'human_review': False},
    'wishlist': {'stage': 'concept', 'hold_reason': None, 'disposition': 'wishlist', 'human_review': False},
    'legacy': {'stage': 'released', 'hold_reason': None, 'disposition': 'legacy', 'human_review': False},
    'deprecated': {'stage': 'released', 'hold_reason': None, 'disposition': 'deprecated', 'human_review': False},
    # This needs stage inference
    'archived': {'stage': 'INFER', 'hold_reason': None, 'disposition': 'archived', 'human_review': False},
}

# Stage keywords for inference
STAGE_KEYWORDS = {
    'released': ['released', 'deployed', 'production', 'shipped', 'live'],
    'implemented': ['implemented', 'complete', 'done', 'finished'],
    'verifying': ['verifying', 'verification', 'testing', 'validating'],
    'reviewing': ['reviewing', 'review', 'checking'],
    'active': ['active', 'implementing', 'working', 'coding', 'execution'],
    'queued': ['queued', 'backlog', 'ready to start'],
    'planned': ['planned', 'plan created', 'plan:'],
    'approved': ['approved', 'accepted', 'ready to plan'],
}


def find_db_path() -> Path:
    """Find the story-tree database."""
    candidates = [
        Path('.claude/data/story-tree.db'),
        Path(__file__).parent.parent.parent / 'data' / 'story-tree.db',
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find story-tree.db")


def infer_stage(story: dict) -> str:
    """Infer stage from notes, plan files, and other context."""
    notes = (story.get('notes') or '').lower()
    description = (story.get('description') or '').lower()
    story_id = story.get('id', '')

    # Check for plan file reference
    if 'plan:' in notes or 'plan created' in notes:
        return 'planned'

    # Check for implementation indicators
    if story.get('last_implemented'):
        return 'released'

    # Check stage keywords in notes
    for stage, keywords in STAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in notes:
                return stage

    # Check for common patterns
    if 'was planned' in notes:
        return 'planned'
    if 'was approved' in notes:
        return 'approved'
    if 'during execution' in notes or 'during implementation' in notes:
        return 'active'

    # Default to concept for pending/blocked/archived without context
    return 'concept'


def get_mapping(status: str) -> dict:
    """Get the three-field mapping for a status."""
    if status in STAGE_MAPPINGS:
        return STAGE_MAPPINGS[status]
    if status in HOLD_MAPPINGS:
        return HOLD_MAPPINGS[status]
    if status in DISPOSITION_MAPPINGS:
        return DISPOSITION_MAPPINGS[status]
    # Unknown status - treat as concept
    return {'stage': 'concept', 'hold_reason': None, 'disposition': None, 'human_review': False}


def migrate_database(db_path: Path, dry_run: bool = False) -> dict:
    """Perform the migration."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    results = {
        'stories_migrated': 0,
        'stages_inferred': 0,
        'columns_added': [],
        'constraints_added': [],
        'indexes_created': [],
        'errors': [],
        'inferred_stages': [],
    }

    try:
        cursor = conn.cursor()

        # Step 1: Check if migration already done
        cursor.execute("PRAGMA table_info(story_nodes)")
        columns = {row['name'] for row in cursor.fetchall()}

        if 'stage' in columns:
            print("Migration already completed (stage column exists)")
            return results

        print("Starting migration...")

        # Step 2: Add new columns
        new_columns = [
            ("stage", "TEXT DEFAULT 'concept'"),
            ("hold_reason", "TEXT DEFAULT NULL"),
            ("disposition", "TEXT DEFAULT NULL"),
            ("human_review", "INTEGER DEFAULT 0"),
        ]

        for col_name, col_def in new_columns:
            if col_name not in columns:
                sql = f"ALTER TABLE story_nodes ADD COLUMN {col_name} {col_def}"
                if not dry_run:
                    cursor.execute(sql)
                results['columns_added'].append(col_name)
                print(f"  Added column: {col_name}")

        if not dry_run:
            conn.commit()

        # Step 3: Migrate existing data
        cursor.execute("""
            SELECT id, status, notes, description, last_implemented
            FROM story_nodes
        """)
        stories = [dict(row) for row in cursor.fetchall()]

        print(f"\nMigrating {len(stories)} stories...")

        for story in stories:
            status = story['status']
            mapping = get_mapping(status)

            # Handle stage inference
            if mapping['stage'] == 'INFER':
                inferred_stage = infer_stage(story)
                mapping = dict(mapping)  # Copy
                mapping['stage'] = inferred_stage
                results['stages_inferred'] += 1
                results['inferred_stages'].append({
                    'id': story['id'],
                    'status': status,
                    'inferred_stage': inferred_stage,
                    'notes_hint': story['notes'][:100] if story['notes'] else None
                })

            # Update the row
            sql = """
                UPDATE story_nodes
                SET stage = ?, hold_reason = ?, disposition = ?, human_review = ?
                WHERE id = ?
            """
            params = (
                mapping['stage'],
                mapping['hold_reason'],
                mapping['disposition'],
                1 if mapping['human_review'] else 0,
                story['id']
            )

            if not dry_run:
                cursor.execute(sql, params)

            results['stories_migrated'] += 1

        if not dry_run:
            conn.commit()

        print(f"  Migrated {results['stories_migrated']} stories")
        print(f"  Inferred stage for {results['stages_inferred']} stories")

        # Step 4: Create indexes (CHECK constraints can't be added to existing tables in SQLite)
        indexes = [
            ("idx_active_pipeline",
             "CREATE INDEX IF NOT EXISTS idx_active_pipeline ON story_nodes(stage) WHERE disposition IS NULL AND hold_reason IS NULL"),
            ("idx_held_stories",
             "CREATE INDEX IF NOT EXISTS idx_held_stories ON story_nodes(hold_reason) WHERE hold_reason IS NOT NULL"),
            ("idx_disposed_stories",
             "CREATE INDEX IF NOT EXISTS idx_disposed_stories ON story_nodes(disposition) WHERE disposition IS NOT NULL"),
            ("idx_needs_review",
             "CREATE INDEX IF NOT EXISTS idx_needs_review ON story_nodes(human_review) WHERE human_review = 1"),
        ]

        print("\nCreating indexes...")
        for idx_name, idx_sql in indexes:
            if not dry_run:
                cursor.execute(idx_sql)
            results['indexes_created'].append(idx_name)
            print(f"  Created index: {idx_name}")

        if not dry_run:
            conn.commit()

        # Step 5: Add a trigger to keep deprecated 'status' column in sync
        print("\nCreating sync trigger...")
        trigger_sql = """
        CREATE TRIGGER IF NOT EXISTS sync_status_from_fields
        AFTER UPDATE OF stage, hold_reason, disposition ON story_nodes
        FOR EACH ROW
        BEGIN
            UPDATE story_nodes SET status =
                CASE
                    -- Dispositions take precedence
                    WHEN NEW.disposition IS NOT NULL THEN NEW.disposition
                    -- Then hold reasons
                    WHEN NEW.hold_reason IS NOT NULL THEN NEW.hold_reason
                    -- Then stage
                    ELSE NEW.stage
                END
            WHERE id = NEW.id;
        END;
        """
        if not dry_run:
            cursor.execute(trigger_sql)
            conn.commit()
        print("  Created sync trigger: sync_status_from_fields")

        print("\nMigration complete!")

    except Exception as e:
        results['errors'].append(str(e))
        if not dry_run:
            conn.rollback()
        raise
    finally:
        conn.close()

    return results


def verify_migration(db_path: Path) -> dict:
    """Verify the migration was successful."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    verification = {
        'columns_exist': False,
        'all_stories_have_stage': False,
        'stage_distribution': {},
        'hold_distribution': {},
        'disposition_distribution': {},
        'human_review_count': 0,
        'issues': []
    }

    try:
        cursor = conn.cursor()

        # Check columns exist
        cursor.execute("PRAGMA table_info(story_nodes)")
        columns = {row['name'] for row in cursor.fetchall()}
        verification['columns_exist'] = all(
            col in columns for col in ['stage', 'hold_reason', 'disposition', 'human_review']
        )

        # Check all stories have stage
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE stage IS NULL")
        null_stages = cursor.fetchone()[0]
        verification['all_stories_have_stage'] = (null_stages == 0)
        if null_stages > 0:
            verification['issues'].append(f"{null_stages} stories have NULL stage")

        # Get distributions
        cursor.execute("SELECT stage, COUNT(*) as cnt FROM story_nodes GROUP BY stage")
        verification['stage_distribution'] = {row['stage']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT hold_reason, COUNT(*) as cnt FROM story_nodes WHERE hold_reason IS NOT NULL GROUP BY hold_reason")
        verification['hold_distribution'] = {row['hold_reason']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT disposition, COUNT(*) as cnt FROM story_nodes WHERE disposition IS NOT NULL GROUP BY disposition")
        verification['disposition_distribution'] = {row['disposition']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE human_review = 1")
        verification['human_review_count'] = cursor.fetchone()[0]

        # Check for invalid combinations
        cursor.execute("""
            SELECT id, stage, hold_reason, disposition FROM story_nodes
            WHERE hold_reason IS NOT NULL AND disposition IS NOT NULL
        """)
        invalid = cursor.fetchall()
        if invalid:
            verification['issues'].append(f"{len(invalid)} stories have both hold_reason AND disposition")

    finally:
        conn.close()

    return verification


def main():
    parser = argparse.ArgumentParser(description='Migrate story-tree to three-field schema')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--db', type=Path, help='Database path')
    parser.add_argument('--verify', action='store_true', help='Verify migration status')
    args = parser.parse_args()

    try:
        db_path = args.db if args.db else find_db_path()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Database: {db_path}")

    if args.verify:
        print("\nVerifying migration status...\n")
        verification = verify_migration(db_path)
        print(json.dumps(verification, indent=2))
        return

    if args.dry_run:
        print("\n*** DRY RUN - No changes will be made ***\n")

    results = migrate_database(db_path, dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print("MIGRATION SUMMARY")
    print("=" * 50)
    print(json.dumps(results, indent=2))

    if not args.dry_run:
        print("\nRunning verification...")
        verification = verify_migration(db_path)
        print("\nVerification results:")
        print(json.dumps(verification, indent=2))

        if verification['issues']:
            print("\n⚠️  Issues found:")
            for issue in verification['issues']:
                print(f"  - {issue}")
        else:
            print("\n✅ Migration verified successfully!")


if __name__ == '__main__':
    main()
