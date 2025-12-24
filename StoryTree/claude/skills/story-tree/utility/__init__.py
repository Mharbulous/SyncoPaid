"""Story-tree database utilities package.

This package provides consolidated database operations for all story-related skills.
Import from here instead of duplicating database code across skills.
"""

from .story_db_common import (
    # Constants
    DB_PATH,
    MERGEABLE_STATUSES,
    BLOCK_STATUSES,
    CLASSIFICATIONS,
    ACTIONS,
    # Utility functions
    get_connection,
    make_pair_key,
    get_story_version,
    compute_effective_status,
    # Story CRUD operations
    delete_story,
    reject_concept,
    block_concept,
    defer_concept,
    merge_concepts,
    append_note,
)

__all__ = [
    # Constants
    'DB_PATH',
    'MERGEABLE_STATUSES',
    'BLOCK_STATUSES',
    'CLASSIFICATIONS',
    'ACTIONS',
    # Utility functions
    'get_connection',
    'make_pair_key',
    'get_story_version',
    'compute_effective_status',
    # Story CRUD operations
    'delete_story',
    'reject_concept',
    'block_concept',
    'defer_concept',
    'merge_concepts',
    'append_note',
]
