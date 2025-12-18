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
MERGEABLE_STATUSES = {'concept', 'wishlist', 'polish'}

# Statuses that indicate blocking conditions (story not actively progressing)
BLOCK_STATUSES = {'rejected', 'infeasible', 'conflict', 'broken', 'queued', 'pending', 'blocked'}

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
    'REJECT_CONCEPT',    # Human rejection (indicates non-goal)
    'CONFLICT_CONCEPT',  # Algorithm detected overlap (not a goal signal)
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
    - hold_reason: Why work is paused (queued, pending, blocked, broken, etc.)
    - disposition: Terminal state (rejected, archived, wishlist, etc.)

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

    For algorithm-detected conflicts, use conflict_concept() instead.

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


def conflict_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    conflicting_id: str
) -> None:
    """Set concept disposition to conflict (algorithm detected overlap).

    Use this when the ALGORITHM detects overlap with existing story.
    This is NOT a signal about user goals - just prevents duplicate work.

    For human rejections (non-goals), use reject_concept() instead.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to mark as conflict
        conflicting_id: ID of conflicting story (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET disposition = 'conflict',
            notes = COALESCE(notes || char(10), '') || 'Conflicts with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))


def block_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    conflicting_id: str
) -> None:
    """Set concept hold_reason to blocked with conflict note.

    This blocks a concept due to conflict with another story.
    The stage is preserved and hold_reason provides the effective status.
    Sets human_review flag for later attention.

    Args:
        conn: SQLite connection
        concept_id: ID of concept to block
        conflicting_id: ID of conflicting story (for note)

    Note:
        Does NOT commit - caller should commit after all operations complete
    """
    conn.execute('''
        UPDATE story_nodes
        SET hold_reason = 'blocked', human_review = 1,
            notes = COALESCE(notes || char(10), '') || 'Blocked due to conflict with story node ' || ?
        WHERE id = ?
    ''', (conflicting_id, concept_id))


def defer_concept(
    conn: sqlite3.Connection,
    concept_id: str,
    conflicting_id: str
) -> None:
    """Set concept hold_reason to pending for later human review.

    This defers a concept with scope overlap for human review (CI mode).
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
            notes = COALESCE(notes || char(10), '') || 'Scope overlap with ' || ? || ' - needs human review'
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
