#!/usr/bin/env python
"""Story vetting processor - Phase 2: Classification and Resolution (CI Mode)

Processes candidate conflict pairs, classifies them, and executes appropriate
actions. Integrates with vetting_cache to store decisions for future runs.
"""

import sqlite3
import json
import sys
import os
from typing import Dict, List, Tuple, Optional

# Import cache functions
try:
    from vetting_cache import migrate_schema, store_decision
except ImportError:
    # When run as script from different directory
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from vetting_cache import migrate_schema, store_decision

# Constants
# Three-field system mappings (values from COALESCE(disposition, hold_reason, stage))
# - 'concept' = stage='concept'
# - 'wishlist' = disposition='wishlist'
# - 'refine' = hold_reason='refine'
MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}

# Three-field system mappings (values from COALESCE(disposition, hold_reason, stage))
# - 'rejected' = disposition='rejected'
# - 'infeasible' = disposition='infeasible'
# - 'broken' = hold_reason='broken'
# - 'pending' = hold_reason='pending'
# - 'blocked' = hold_reason='blocked'
BLOCK_STATUSES = {'rejected', 'infeasible', 'broken', 'pending', 'blocked'}
DB_PATH = '.claude/data/story-tree.db'
CI_MODE = True  # Always use CI mode in this script

# Statistics counters
stats = {
    'candidates_scanned': 0,
    'deleted': 0,
    'merged': 0,
    'rejected': 0,
    'blocked': 0,
    'skipped': 0,
    'deferred': 0,
    'picked_better': 0,
    'cache_stored': 0,
    'cache_hits_used': 0
}

def get_action(conflict_type: str, status_a: str, status_b: str) -> str:
    """Determine action based on conflict type and statuses."""
    # Ensure concept is always story_a for consistent logic
    if status_b == 'concept' and status_a != 'concept':
        return get_action(conflict_type, status_b, status_a)

    if conflict_type == 'false_positive':
        return 'SKIP'

    if conflict_type == 'duplicate':
        if status_b in MERGEABLE_STATUSES:
            return 'TRUE_MERGE'
        else:
            return 'DELETE_CONCEPT'

    if conflict_type == 'scope_overlap':
        if status_a == 'concept' and status_b == 'concept':
            return 'TRUE_MERGE'
        else:
            # In CI mode, defer to pending instead of human review
            return 'DEFER_PENDING' if CI_MODE else 'HUMAN_REVIEW'

    if conflict_type == 'competing':
        if status_b in MERGEABLE_STATUSES:
            return 'TRUE_MERGE'
        elif status_b in BLOCK_STATUSES:
            return 'BLOCK_CONCEPT'
        else:
            return 'REJECT_CONCEPT'

    if conflict_type == 'incompatible':
        return 'PICK_BETTER'

    return 'SKIP'

def classify_conflict(story_a: Dict, story_b: Dict) -> str:
    """
    Classify the conflict type between two stories using simple heuristics.
    This is a lightweight classification for CI mode - not using LLM analysis.
    """
    # Extract descriptions
    desc_a = story_a['description'].lower()
    desc_b = story_b['description'].lower()
    title_a = story_a['title'].lower()
    title_b = story_b['title'].lower()

    # Very similar titles suggest duplicate
    title_a_words = set(title_a.split())
    title_b_words = set(title_b.split())
    if title_a_words == title_b_words:
        return 'duplicate'

    # Check for specific competing indicators
    competing_keywords = [
        ('sqlite', 'database'),
        ('tkinter', 'gui'),
        ('ui automation', 'manual'),
        ('monthly', 'weekly'),
        ('zip', 'compress')
    ]

    for k1, k2 in competing_keywords:
        if (k1 in desc_a and k2 in desc_b) or (k1 in desc_b and k2 in desc_a):
            return 'competing'

    # Check for parent-child or hierarchical relationships (scope overlap)
    if story_a['id'].startswith(story_b['id'] + '.') or story_b['id'].startswith(story_a['id'] + '.'):
        return 'false_positive'  # Already filtered but double-check

    # Default to scope_overlap for related concepts
    # Most flagged pairs with shared keywords are overlapping scopes
    return 'scope_overlap'

def delete_concept(conn: sqlite3.Connection, concept_id: str) -> None:
    """Delete a concept from the database."""
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (concept_id,))
    conn.execute('DELETE FROM story_nodes WHERE id = ?', (concept_id,))
    stats['deleted'] += 1

def reject_concept(conn: sqlite3.Connection, concept_id: str, conflicting_id: str) -> None:
    """Set concept disposition to rejected with note."""
    conn.execute('''
        UPDATE story_nodes
        SET disposition = 'rejected',
            notes = COALESCE(notes || char(10), '') || 'Conflicts with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    stats['rejected'] += 1

def block_concept(conn: sqlite3.Connection, concept_id: str, conflicting_id: str) -> None:
    """Set concept hold_reason to blocked with note (stage preserved)."""
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'blocked', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Blocked due to conflict with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    stats['blocked'] += 1

def defer_pending(conn: sqlite3.Connection, concept_id: str, conflicting_id: str) -> None:
    """Set concept hold_reason to pending for later human review (stage preserved)."""
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'pending', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Scope overlap with ' || ? || ' - needs human review'
        WHERE id = ?
    ''', (conflicting_id, concept_id))
    stats['deferred'] += 1

def merge_concepts(conn: sqlite3.Connection, keep_id: str, delete_id: str,
                   merged_title: str, merged_desc: str) -> None:
    """Merge two concepts into one."""
    conn.execute('''
        UPDATE story_nodes
        SET title = ?, description = ?,
            notes = COALESCE(notes || char(10), '') || 'Merged from story node ' || ?
        WHERE id = ?
    ''', (merged_title, merged_desc, delete_id, keep_id))
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (delete_id,))
    conn.execute('DELETE FROM story_nodes WHERE id = ?', (delete_id,))
    stats['merged'] += 1

def simple_merge(story_a: Dict, story_b: Dict) -> Tuple[str, str]:
    """
    Simple merge logic for CI mode - combine titles and descriptions.
    Returns (merged_title, merged_description)
    """
    # Use the shorter, more concise title
    merged_title = story_a['title'] if len(story_a['title']) < len(story_b['title']) else story_b['title']

    # Combine descriptions - take user story from first, append unique acceptance criteria
    merged_desc = story_a['description']

    # Extract acceptance criteria lines from both
    criteria_b = [line for line in story_b['description'].split('\n') if line.strip().startswith('- [')]
    if criteria_b:
        merged_desc += '\n' + '\n'.join(criteria_b)

    return merged_title, merged_desc

def process_candidate(conn: sqlite3.Connection, candidate: Dict) -> None:
    """Process a single candidate pair and cache the decision."""
    stats['candidates_scanned'] += 1

    story_a = candidate['story_a']
    story_b = candidate['story_b']

    # Skip if neither is a concept
    if story_a['status'] != 'concept' and story_b['status'] != 'concept':
        stats['skipped'] += 1
        return

    # Check if we have a cached classification from Phase 1 filtering
    cached_classification = candidate.get('cached_classification')
    if cached_classification:
        conflict_type = cached_classification
        stats['cache_hits_used'] += 1
    else:
        # Classify the conflict
        conflict_type = classify_conflict(story_a, story_b)

    # Get the action
    action = get_action(conflict_type, story_a['status'], story_b['status'])

    # Store original IDs for caching (before any swaps)
    original_id_a = story_a['id']
    original_id_b = story_b['id']

    # Ensure concept is always story_a for execution
    if story_b['status'] == 'concept' and story_a['status'] != 'concept':
        story_a, story_b = story_b, story_a

    # Execute action
    if action == 'SKIP':
        stats['skipped'] += 1

    elif action == 'DELETE_CONCEPT':
        delete_concept(conn, story_a['id'])

    elif action == 'REJECT_CONCEPT':
        reject_concept(conn, story_a['id'], story_b['id'])

    elif action == 'BLOCK_CONCEPT':
        block_concept(conn, story_a['id'], story_b['id'])

    elif action == 'DEFER_PENDING':
        defer_pending(conn, story_a['id'], story_b['id'])

    elif action == 'TRUE_MERGE':
        # Determine which to keep (lower ID = more established)
        if story_a['id'] < story_b['id']:
            keep_id, delete_id = story_a['id'], story_b['id']
            keep_story, delete_story = story_a, story_b
        else:
            keep_id, delete_id = story_b['id'], story_a['id']
            keep_story, delete_story = story_b, story_a

        merged_title, merged_desc = simple_merge(keep_story, delete_story)
        merge_concepts(conn, keep_id, delete_id, merged_title, merged_desc)

    elif action == 'PICK_BETTER':
        # For CI mode, use simple heuristic: prefer story with more detailed description
        if len(story_a['description']) >= len(story_b['description']):
            delete_concept(conn, story_b['id'])
        else:
            delete_concept(conn, story_a['id'])
        stats['picked_better'] += 1

    # Store decision in cache (only if not already cached)
    if not cached_classification:
        try:
            store_decision(conn, original_id_a, original_id_b, conflict_type, action)
            stats['cache_stored'] += 1
        except Exception:
            # Don't fail on cache errors - caching is best-effort
            pass

def main():
    # Read candidates from stdin
    candidates_data = json.load(sys.stdin)
    candidates = candidates_data['candidates']

    print(f"Processing {len(candidates)} candidates in CI mode...\n", file=sys.stderr)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Ensure schema is migrated (adds version column and vetting_decisions table)
    migration_result = migrate_schema(conn)
    if migration_result['version_added'] or migration_result['table_created']:
        print(f"Schema migration: {migration_result}", file=sys.stderr)

    try:
        # Process each candidate
        for candidate in candidates:
            process_candidate(conn, candidate)

        # Commit all changes
        conn.commit()

        # Print summary
        print("\nSTORY VETTING COMPLETE (CI MODE)", file=sys.stderr)
        print("=" * 40, file=sys.stderr)
        print(f"\nCandidates scanned: {stats['candidates_scanned']}", file=sys.stderr)
        print("Actions taken:", file=sys.stderr)
        print(f"  - Deleted: {stats['deleted']} duplicate concepts", file=sys.stderr)
        print(f"  - Merged: {stats['merged']} concept pairs", file=sys.stderr)
        print(f"  - Rejected: {stats['rejected']} competing concepts", file=sys.stderr)
        print(f"  - Blocked: {stats['blocked']} concepts", file=sys.stderr)
        print(f"  - Skipped: {stats['skipped']} false positives", file=sys.stderr)
        print(f"  - Deferred to pending: {stats['deferred']} scope overlaps", file=sys.stderr)
        print(f"  - Picked better: {stats['picked_better']} incompatible pairs", file=sys.stderr)
        print("\nCache operations:", file=sys.stderr)
        print(f"  - Decisions cached: {stats['cache_stored']}", file=sys.stderr)
        print(f"  - Cache hits used: {stats['cache_hits_used']}", file=sys.stderr)

        if stats['deferred'] > 0:
            print(f"\n{stats['deferred']} concepts set to 'pending' status for later human review.", file=sys.stderr)

        # Output summary JSON for orchestrator
        summary = {
            'status': 'success',
            'candidates_scanned': stats['candidates_scanned'],
            'actions': stats
        }
        print(json.dumps(summary))

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}", file=sys.stderr)
        print(json.dumps({'status': 'error', 'message': str(e)}))
        sys.exit(1)

    finally:
        conn.close()

if __name__ == '__main__':
    main()
