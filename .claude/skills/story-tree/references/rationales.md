# Design Rationale

Consult when instructions seem counter-intuitive or you're tempted to deviate.

## Why Closure Table

Stores ALL ancestor-descendant paths, enabling subtree queries without recursion and O(1) depth. Trade-off: O(n*depth) storage rows.

## Database Location

`.claude/data/story-tree.db` (tracked in git for history)

## Status Exclusions

Priority algorithm excludes stories where:
- `stage = 'concept'` (not yet approved)
- `hold_reason IS NOT NULL` (queued/pending/blocked/broken/polish)
- `disposition IS NOT NULL` (rejected/archived/etc)

## Dynamic Capacity

`effective_capacity = capacity_override OR (3 + implemented/ready children)`

New nodes start with capacity 3, grows as children complete. Forces depth before breadth.

## Max 3 Concepts Per Node

Combined with dynamic capacity (starts at 3): prevents shallow, speculative growth.

## Checkpoint Failures

Log reason before fallback to help users understand why analysis is slower:
- "No checkpoint found. Running full 30-day scan."
- "Checkpoint abc123 no longer exists. Running full 30-day scan."
