#!/usr/bin/env python
"""Common database utilities for story-tree operations.

This module consolidates database operations used across multiple story-related skills
to ensure DRY principles and consistent behavior.

Usage:
    # From story-vetting scripts:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
    from story_db_common import (
        DB_PATH, get_connection, make_pair_key, delete_story,
        reject_concept, block_concept, defer_concept, merge_concepts
    )
"""

import sqlite3
from typing import Optional


# =============================================================================
# Constants
# =============================================================================

DB_PATH = '.claude/data/story-tree.db'

# Three-field workflow system status sets
# These represent computed status values from COALESCE(disposition, hold_reason, stage)

# Statuses that allow merging (early-stage concepts)
# Note: concept=stage, wishlist/polish/refine=hold_reason
MERGEABLE_STATUSES = {'concept', 'wishlist', 'polish', 'refine'}

# Statuses that indicate blocking conditions (story not actively progressing)
BLOCK_STATUSES = {'rejected', 'infeasible', 'duplicative', 'broken', 'queued', 'pending', 'blocked', 'conflict'}

# Valid vetting classification types
CLASSIFICATIONS = {
    'duplicate',
    'scope_overlap',
    'competing',
    'incompatible',
    'false_positive'
}

# Valid vetting action types
ACTIONS = {
    'SKIP',
    'DELETE_CONCEPT',
    'REJECT_CONCEPT',      # Human rejection (indicates non-goal)
    'DUPLICATIVE_CONCEPT', # Algorithm detected duplicate/overlap (not a goal signal)
    'BLOCK_CONCEPT',
    'TRUE_MERGE',
    'PICK_BETTER',
    'HUMAN_REVIEW',
    'DEFER_PENDING'
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Get a database connection with standard settings.

    Args:
        db_path: Path to the SQLite database (default: DB_PATH)

    Returns:
        sqlite3.Connection with foreign keys enabled
    """
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def make_pair_key(id_a: str, id_b: str) -> str:
    """Create canonical pair key with smaller ID first.

    This ensures consistent lookup regardless of comparison order.
    Used for caching vetting decisions.

    Examples:
        make_pair_key("1.8.4", "1.1") -> "1.1|1.8.4"
        make_pair_key("1.1", "1.8.4") -> "1.1|1.8.4"

    Args:
        id_a: First story ID
        id_b: Second story ID

    Returns:
        Canonical pair key string "smaller_id|larger_id"
    """
    if id_a < id_b:
        return f"{id_a}|{id_b}"
    else:
        return f"{id_b}|{id_a}"


def get_story_version(conn: sqlite3.Connection, story_id: str) -> int:
    """Get current version of a story.

    Args:
        conn: SQLite connection
        story_id: Story ID to look up

    Returns:
        Version number (defaults to 1 if story doesn't exist or version is NULL)
    """
    row = conn.execute(
        'SELECT version FROM story_nodes WHERE id = ?', (story_id,)
    ).fetchone()
    return (row[0] if row and row[0] else 1)


def compute_effective_status(
    stage: Optional[str],
    hold_reason: Optional[str],
    disposition: Optional[str]
) -> str:
    """Compute effective status from three-field workflow system.

    Implements: COALESCE(disposition, hold_reason, stage)

    The three-field system uses:
    - stage: Position in pipeline (concept, approved, planned, active, etc.)
    - hold_reason: Why work is paused (queued, pending, blocked, wishlist, etc.)
    - disposition: Terminal state (rejected, archived, infeasible, etc.)

    Args:
        stage: Current pipeline stage
        hold_reason: Current hold reason (if any)
        disposition: Current disposition (if any)

    Returns:
        Effective status string
    """
    return disposition or hold_reason or stage or 'unknown'


def append_note(existing_notes: Optional[str], new_note: str) -> str:
    """Append a note to existing notes with newline separator.

    Args:
        existing_notes: Current notes (may be None)
        new_note: Note to append

    Returns:
        Combined notes string
    """
    if existing_notes:
        return existing_notes + '\n' + new_note
    return new_note


# =============================================================================
# Story CRUD Operations
# =============================================================================

def delete_story(conn: sqlite3.Connection, story_id: str) -> None:
    """Delete a story and cascade to closure table.

    This handles the proper deletion order for the closure table pattern:
    1. Delete from story_paths (closure table entries)
    2. Delete from story_nodes

    Args:
        conn: SQLite connection
        story_id: ID of story to delete

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (story_id,))
    conn.execute('DELETE FROM story_nodes WHERE id = ?', (story_id,))


def reject_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    reason: str
) -> None:
    """Set concept disposition to rejected (human decision, indicates non-goal).

    Use this when a HUMAN decides not to implement a concept.
    The rejection is a meaningful signal about user goals/non-goals.

    For algorithm-detected duplicates, use duplicative_concept() instead.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to reject
        reason: Human-provided reason for rejection

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET disposition = 'rejected',
            notes = COALESCE(notes || char(10), '') || ?
        WHERE id = ?
    ''', (reason, concept_id))


def duplicative_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    duplicate_of_id: str
) -> None:
    """Set concept disposition to duplicative (algorithm detected duplicate/overlap).

    Use this when the ALGORITHM detects duplicate or overlap with existing story.
    This is NOT a signal about user goals - just prevents duplicate work.

    For human rejections (non-goals), use reject_concept() instead.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to mark as duplicative
        duplicate_of_id: ID of the existing story this duplicates (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET disposition = 'duplicative',
            notes = COALESCE(notes || char(10), '') || 'Duplicates story node ' || ?
        WHERE id = ?
    ''', (duplicate_of_id, concept_id))


def block_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    blocking_id: str
) -> None:
    """Set concept hold_reason to blocked due to dependency on another story.

    This blocks a concept because it depends on another story being completed.
    The stage is preserved and hold_reason provides the effective status.
    Sets human_review flag for later attention.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to block
        blocking_id: ID of blocking story (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'blocked', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Blocked by dependency on story node ' || ?
        WHERE id = ?
    ''', (blocking_id, concept_id))


def defer_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    conflicting_id: str
) -> None:
    """Set concept hold_reason to refine due to scope overlap.

    This marks a concept for refinement when scope overlap is detected.
    The stage is preserved and hold_reason provides the effective status.
    Sets human_review flag for attention.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to defer
        conflicting_id: ID of related story (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'pending', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Scope overlap detected with story-node IDs: ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))


def conflict_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    conflicting_id: str
) -> None:
    """Set concept hold_reason to conflict (inconsistent with another story, needs resolution).

    Use this when two stories are INCONSISTENT (mutually exclusive approaches)
    and a human has NOT yet decided which one to pursue.

    For algorithm-detected duplicates, use duplicative_concept() instead.
    For external dependencies, use block_concept() instead.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to mark as conflicting
        conflicting_id: ID of the conflicting story (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'conflict', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Inconsistent with story node ' || ? || ' - needs resolution'
        WHERE id = ?
    ''', (conflicting_id, concept_id))


def merge_concepts(
    conn: sqlite3.Connection,
    keep_id: str,
    delete_id: str,
    merged_title: str,
    merged_description: str
) -> None:
    """Merge two concepts: update one, delete the other.

    The kept story receives the merged title and description, plus a note
    indicating it was merged from the deleted story.

    Args:
        conn: SQLite connection
        keep_id: ID of story to keep
        delete_id: ID of story to delete
        merged_title: New merged title
        merged_description: New merged description

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    # Update the kept story
    conn.execute('''
        UPDATE story_nodes
        SET title = ?, description = ?,
            notes = COALESCE(notes || char(10), '') || 'Merged from story node ' || ?
        WHERE id = ?
    ''', (merged_title, merged_description, delete_id, keep_id))

    # Delete the other story
    delete_story(conn, delete_id)


# =============================================================================
# Tree Structure Validation and Reorganization
# =============================================================================

def get_expected_parent_id(story_id: str) -> Optional[str]:
    """Determine expected parent ID based on story ID format.

    Args:
        story_id: The story ID to analyze

    Returns:
        Expected parent ID, or None if cannot determine
    """
    if story_id == 'root':
        return None
    elif '.' in story_id:
        # Decimal ID: parent is everything before last dot
        return story_id.rsplit('.', 1)[0]
    elif story_id.isdigit():
        # Plain integer: parent should be root
        return 'root'
    else:
        # Invalid format
        return None


def validate_tree_structure(conn: sqlite3.Connection) -> dict:
    """Find structural issues in the story tree.

    Identifies:
    - Nodes with invalid ID format for their level (decimal ID at root level)
    - Orphaned nodes (exist in story_nodes but missing story_paths entries)
    - Nodes with ID prefix not matching parent ID
    - Missing self-path entries (depth=0)

    Args:
        conn: SQLite connection

    Returns:
        Dictionary with issue categories:
        {
            'invalid_root_children': [...],  # Decimal IDs at root level
            'orphaned_nodes': [...],         # Missing from story_paths
            'missing_self_paths': [...],     # No depth=0 entry
            'parent_mismatch': [...],        # ID doesn't match actual parent
            'invalid_id_format': [...]       # Malformed IDs
        }
    """
    issues = {
        'invalid_root_children': [],
        'orphaned_nodes': [],
        'missing_self_paths': [],
        'parent_mismatch': [],
        'invalid_id_format': []
    }

    # Get all story nodes
    all_nodes = conn.execute(
        'SELECT id, title FROM story_nodes WHERE id != ?', ('root',)
    ).fetchall()

    for (node_id, title) in all_nodes:
        # Check for invalid ID format (should be integer or decimal like 1.2.3)
        if node_id != 'root':
            parts = node_id.split('.')
            if not all(p.isdigit() for p in parts):
                issues['invalid_id_format'].append({
                    'id': node_id,
                    'title': title,
                    'reason': 'ID contains non-numeric parts'
                })
                continue

        # Check for missing self-path (depth=0)
        self_path = conn.execute(
            'SELECT 1 FROM story_paths WHERE ancestor_id = ? AND descendant_id = ? AND depth = 0',
            (node_id, node_id)
        ).fetchone()
        if not self_path:
            issues['missing_self_paths'].append({
                'id': node_id,
                'title': title
            })

        # Check if orphaned (no paths at all)
        any_path = conn.execute(
            'SELECT 1 FROM story_paths WHERE descendant_id = ?', (node_id,)
        ).fetchone()
        if not any_path:
            issues['orphaned_nodes'].append({
                'id': node_id,
                'title': title
            })
            continue  # Can't check parent if orphaned

        # Get actual parent from story_paths (depth=1 ancestor)
        actual_parent = conn.execute('''
            SELECT ancestor_id FROM story_paths
            WHERE descendant_id = ? AND depth = 1
        ''', (node_id,)).fetchone()

        expected_parent = get_expected_parent_id(node_id)

        # Check for invalid root children (decimal ID with root parent)
        if actual_parent and actual_parent[0] == 'root' and '.' in node_id:
            issues['invalid_root_children'].append({
                'id': node_id,
                'title': title,
                'reason': f'Root child should have integer ID, not "{node_id}"'
            })

        # Check for parent mismatch
        if actual_parent and expected_parent and actual_parent[0] != expected_parent:
            issues['parent_mismatch'].append({
                'id': node_id,
                'title': title,
                'actual_parent': actual_parent[0],
                'expected_parent': expected_parent
            })

    return issues


def rename_story(
    conn: sqlite3.Connection,
    old_id: str,
    new_id: str
) -> list:
    """Rename a story and all its descendants.

    Uses temporary IDs to avoid conflicts during rename.
    Updates story_nodes, story_paths, story_commits, and vetting_decisions.

    Args:
        conn: SQLite connection
        old_id: Current story ID
        new_id: New story ID

    Returns:
        List of (old_id, new_id) tuples for all renamed nodes

    Note:
        Does NOT commit - caller should commit after all operations complete
        Caller should disable foreign keys before calling if needed
    """
    # Get all descendant IDs (including self)
    descendants = conn.execute('''
        SELECT descendant_id FROM story_paths
        WHERE ancestor_id = ? AND depth >= 0
        ORDER BY depth ASC
    ''', (old_id,)).fetchall()

    # Build rename map: old_id.X.Y → new_id.X.Y
    renames = []
    for (desc_id,) in descendants:
        if desc_id == old_id:
            renames.append((desc_id, new_id))
        elif desc_id.startswith(old_id + '.'):
            suffix = desc_id[len(old_id):]
            renames.append((desc_id, new_id + suffix))

    # Step 1: Rename to temporary IDs to avoid conflicts
    temp_prefix = '__temp_rename__'
    for old, new in renames:
        temp_id = temp_prefix + old
        # Update story_nodes
        conn.execute('UPDATE story_nodes SET id = ? WHERE id = ?', (temp_id, old))
        # Update story_paths (both ancestor and descendant references)
        conn.execute('UPDATE story_paths SET ancestor_id = ? WHERE ancestor_id = ?', (temp_id, old))
        conn.execute('UPDATE story_paths SET descendant_id = ? WHERE descendant_id = ?', (temp_id, old))
        # Update story_commits if table exists
        try:
            conn.execute('UPDATE story_commits SET story_id = ? WHERE story_id = ?', (temp_id, old))
        except sqlite3.OperationalError:
            pass  # Table doesn't exist
        # Update vetting_decisions if table exists
        try:
            conn.execute('UPDATE vetting_decisions SET story_a_id = ? WHERE story_a_id = ?', (temp_id, old))
            conn.execute('UPDATE vetting_decisions SET story_b_id = ? WHERE story_b_id = ?', (temp_id, old))
        except sqlite3.OperationalError:
            pass  # Table doesn't exist

    # Step 2: Rename from temporary to final IDs
    for old, new in renames:
        temp_id = temp_prefix + old
        # Update story_nodes
        conn.execute('UPDATE story_nodes SET id = ? WHERE id = ?', (new, temp_id))
        # Update story_paths
        conn.execute('UPDATE story_paths SET ancestor_id = ? WHERE ancestor_id = ?', (new, temp_id))
        conn.execute('UPDATE story_paths SET descendant_id = ? WHERE descendant_id = ?', (new, temp_id))
        # Update story_commits if exists
        try:
            conn.execute('UPDATE story_commits SET story_id = ? WHERE story_id = ?', (new, temp_id))
        except sqlite3.OperationalError:
            pass
        # Update vetting_decisions if exists
        try:
            conn.execute('UPDATE vetting_decisions SET story_a_id = ? WHERE story_a_id = ?', (new, temp_id))
            conn.execute('UPDATE vetting_decisions SET story_b_id = ? WHERE story_b_id = ?', (new, temp_id))
        except sqlite3.OperationalError:
            pass

    return renames


def rebuild_paths(conn: sqlite3.Connection, node_id: str) -> None:
    """Rebuild story_paths for a node based on its ID hierarchy.

    Reconstructs the closure table entries by:
    1. Deleting existing paths for the node
    2. Inserting self-path (depth=0)
    3. Copying parent's ancestors with incremented depth

    Args:
        conn: SQLite connection
        node_id: Story ID to rebuild paths for

    Note:
        Does NOT commit - caller should commit after all operations complete
        Only rebuilds paths for the specific node, not descendants
    """
    # Delete existing paths where this node is descendant
    conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (node_id,))

    # Insert self-path
    conn.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        VALUES (?, ?, 0)
    ''', (node_id, node_id))

    # Find parent from ID format
    parent_id = get_expected_parent_id(node_id)

    if parent_id:
        # Verify parent exists
        parent_exists = conn.execute(
            'SELECT 1 FROM story_nodes WHERE id = ?', (parent_id,)
        ).fetchone()

        if parent_exists:
            # Copy parent's ancestors and increment depth
            conn.execute('''
                INSERT INTO story_paths (ancestor_id, descendant_id, depth)
                SELECT ancestor_id, ?, depth + 1
                FROM story_paths WHERE descendant_id = ?
            ''', (node_id, parent_id))


def rebuild_paths_recursive(conn: sqlite3.Connection, node_id: str) -> int:
    """Rebuild story_paths for a node and all its descendants.

    Args:
        conn: SQLite connection
        node_id: Story ID to start rebuilding from

    Returns:
        Number of nodes rebuilt

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    # Get all descendants based on ID prefix matching
    if node_id == 'root':
        # All nodes are descendants of root
        descendants = conn.execute(
            "SELECT id FROM story_nodes WHERE id != 'root' ORDER BY LENGTH(id)"
        ).fetchall()
    else:
        # Find by ID prefix
        descendants = conn.execute('''
            SELECT id FROM story_nodes
            WHERE id = ? OR id LIKE ? ESCAPE '\\'
            ORDER BY LENGTH(id)
        ''', (node_id, node_id.replace('_', '\\_').replace('%', '\\%') + '.%')).fetchall()

    count = 0
    for (desc_id,) in descendants:
        rebuild_paths(conn, desc_id)
        count += 1

    return count


def move_story(
    conn: sqlite3.Connection,
    story_id: str,
    new_parent_id: str
) -> str:
    """Move a story node to a new parent with appropriate ID renaming.

    Validates the move, generates appropriate new ID, and updates
    all references including descendants.

    Args:
        conn: SQLite connection
        story_id: ID of story to move
        new_parent_id: ID of new parent (use 'root' for top level)

    Returns:
        New ID of the moved story

    Raises:
        ValueError: If move is invalid (circular, parent doesn't exist, etc.)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    # Validate story exists
    story = conn.execute(
        'SELECT id, title FROM story_nodes WHERE id = ?', (story_id,)
    ).fetchone()
    if not story:
        raise ValueError(f"Story '{story_id}' does not exist")

    # Validate new parent exists
    parent = conn.execute(
        'SELECT id FROM story_nodes WHERE id = ?', (new_parent_id,)
    ).fetchone()
    if not parent:
        raise ValueError(f"Parent '{new_parent_id}' does not exist")

    # Check for circular reference (can't move to self or descendant)
    if story_id == new_parent_id:
        raise ValueError("Cannot move story to itself")

    is_descendant = conn.execute('''
        SELECT 1 FROM story_paths
        WHERE ancestor_id = ? AND descendant_id = ?
    ''', (story_id, new_parent_id)).fetchone()
    if is_descendant:
        raise ValueError(f"Cannot move story to its own descendant '{new_parent_id}'")

    # Generate new ID based on new parent
    if new_parent_id == 'root':
        # Find next available integer ID
        existing = conn.execute('''
            SELECT CAST(sn.id AS INTEGER) FROM story_nodes sn
            JOIN story_paths sp ON sn.id = sp.descendant_id
            WHERE sp.ancestor_id = 'root' AND sp.depth = 1
            AND sn.id GLOB '[0-9]*' AND sn.id NOT LIKE '%.%'
        ''').fetchall()
        existing_ints = sorted([r[0] for r in existing if r[0]])
        next_int = 1
        for e in existing_ints:
            if e == next_int:
                next_int = e + 1
        new_id = str(next_int)
    else:
        # Find next available child ID under new parent
        existing = conn.execute('''
            SELECT descendant_id FROM story_paths
            WHERE ancestor_id = ? AND depth = 1
        ''', (new_parent_id,)).fetchall()
        existing_children = [r[0] for r in existing]

        # Find max child number
        max_child = 0
        prefix = new_parent_id + '.'
        for child in existing_children:
            if child.startswith(prefix):
                suffix = child[len(prefix):]
                if '.' not in suffix and suffix.isdigit():
                    max_child = max(max_child, int(suffix))

        new_id = f"{new_parent_id}.{max_child + 1}"

    # Perform the rename (handles descendants automatically)
    rename_story(conn, story_id, new_id)

    # Rebuild paths for the moved node and descendants
    rebuild_paths_recursive(conn, new_id)

    return new_id


def get_next_child_id(conn: sqlite3.Connection, parent_id: str) -> str:
    """Get the next available child ID for a parent.

    Args:
        conn: SQLite connection
        parent_id: Parent story ID (use 'root' for top level)

    Returns:
        Next available child ID
    """
    if parent_id == 'root':
        # Find next available integer ID
        existing = conn.execute('''
            SELECT CAST(sn.id AS INTEGER) FROM story_nodes sn
            JOIN story_paths sp ON sn.id = sp.descendant_id
            WHERE sp.ancestor_id = 'root' AND sp.depth = 1
            AND sn.id GLOB '[0-9]*' AND sn.id NOT LIKE '%.%'
        ''').fetchall()
        existing_ints = sorted([r[0] for r in existing if r[0]])
        next_int = 1
        for e in existing_ints:
            if e == next_int:
                next_int = e + 1
        return str(next_int)
    else:
        # Find next available child ID under parent
        existing = conn.execute('''
            SELECT descendant_id FROM story_paths
            WHERE ancestor_id = ? AND depth = 1
        ''', (parent_id,)).fetchall()

        max_child = 0
        prefix = parent_id + '.'
        for (child,) in existing:
            if child.startswith(prefix):
                suffix = child[len(prefix):]
                if '.' not in suffix and suffix.isdigit():
                    max_child = max(max_child, int(suffix))

        return f"{parent_id}.{max_child + 1}"


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == '__main__':
    import sys

    print("Story DB Common Utilities")
    print("=" * 40)
    print(f"DB_PATH: {DB_PATH}")
    print(f"MERGEABLE_STATUSES: {MERGEABLE_STATUSES}")
    print(f"BLOCK_STATUSES: {BLOCK_STATUSES}")
    print()
    print("Pair key examples:")
    print(f"  make_pair_key('1.8.4', '1.1') = '{make_pair_key('1.8.4', '1.1')}'")
    print(f"  make_pair_key('1.1', '1.8.4') = '{make_pair_key('1.1', '1.8.4')}'")
    print()
    print("Status computation examples:")
    print(f"  compute_effective_status('concept', None, None) = '{compute_effective_status('concept', None, None)}'")
    print(f"  compute_effective_status('concept', 'blocked', None) = '{compute_effective_status('concept', 'blocked', None)}'")
    print(f"  compute_effective_status('concept', 'blocked', 'rejected') = '{compute_effective_status('concept', 'blocked', 'rejected')}'")
    print()
    print("Expected parent ID examples:")
    print(f"  get_expected_parent_id('root') = {get_expected_parent_id('root')}")
    print(f"  get_expected_parent_id('5') = '{get_expected_parent_id('5')}'")
    print(f"  get_expected_parent_id('5.2') = '{get_expected_parent_id('5.2')}'")
    print(f"  get_expected_parent_id('5.2.3') = '{get_expected_parent_id('5.2.3')}'")
    print()
    print("Tree Reorganization Functions:")
    print("  - validate_tree_structure(conn) -> dict of issues")
    print("  - rename_story(conn, old_id, new_id) -> list of renames")
    print("  - rebuild_paths(conn, node_id) -> None")
    print("  - rebuild_paths_recursive(conn, node_id) -> count")
    print("  - move_story(conn, story_id, new_parent_id) -> new_id")
    print("  - get_next_child_id(conn, parent_id) -> next_id")