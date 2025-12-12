# Story Tree Design Rationale

This document explains the rationale behind key design decisions in the story-tree skill. Consult this when:
- Instructions seem counter-intuitive
- You're tempted to deviate from the prescribed approach
- Questions arise about why something works a certain way

## Storage Decisions

### Why SQLite over JSON

The skill uses SQLite with a closure table pattern instead of a JSON file:

- **Scales to 500+ stories** without performance issues
- **Single SQL query** replaces recursive tree traversal
- **Atomic transactions** prevent data corruption
- **Efficient queries** for priority calculation

JSON files become unwieldy and slow with large trees, requiring full file reads and recursive traversal for every operation.

### Why Database is Separate from Skill Folder

The skill definition files (SKILL.md, schema.sql, lib/, docs/) are meant to be **copied between projects**. The database contains **project-specific data** and should not be copied to other projects.

However, the database **should be tracked in version control** for the current project to maintain history of your backlog evolution.

Location: `.claude/data/story-tree.db` (not in `.claude/skills/`)

## Status Filter Decisions

### Excluded Statuses

The priority algorithm excludes nodes with these statuses (the name explains why):

- `concept`: Unapproved - await human review first
- `rejected`: Human decided against it
- `deprecated`: No longer relevant
- `infeasible`: Cannot be built
- `bugged`: Broken - fix first before expanding

All other statuses are eligible for expansion.

### Why Allow Human Override

Users may request adding concepts to nodes that don't meet the status filter. This is allowed because:
- Ideas come at unexpected times and will be forgotten if not recorded
- Users may have context about upcoming implementations
- Some concepts are worth tracking even for incomplete features

The skill trusts explicit user intent over its own filtering rules.

## Capacity and Generation Limits

### Dynamic Capacity

Capacity is computed as: `3 + count of implemented/ready children`

This self-balancing approach:
- New nodes start with capacity 3
- Capacity grows as children are completed
- Forces depth (implementing what exists) before breadth (adding more concepts)
- Tree grows organically based on actual progress, not speculation

### Why Maximum 3 Concepts Per Node Per Invocation

Combined with dynamic capacity starting at 3, this creates natural pacing:
- First pass: add up to 3 concepts (fills initial capacity)
- Implement some children → capacity grows
- Next pass: add more concepts as earned

Without this limit, the tree would grow shallow and speculative.

## Logging Decisions

### Why Log Checkpoint Validation Failures

When the commit checkpoint is missing or invalid (rebased away), the skill logs the reason before falling back to a full 30-day scan:
- "No checkpoint found. Running full 30-day scan."
- "Checkpoint `abc123` no longer exists (likely rebased). Running full 30-day scan."

This helps users understand why analysis is slower than expected. Without this logging, users might think something is broken when it's actually working correctly.

## Version History

- v2.4.0 (2025-12-12): **Intuitive rules** - (1) Status filter changed to blacklist (concept, rejected, deprecated, infeasible, bugged); (2) Dynamic capacity: `3 + implemented/ready children`; (3) Optional capacity override in schema.
- v2.3.0 (2025-12-12): **Progressive context disclosure** - Moved rationale/design decisions to `docs/rationale.md` to reduce context load on every invocation.
- v2.2.0 (2025-12-12): **Progressive context disclosure** - Moved database initialization details to `lib/initialization.md` to reduce context load on every invocation (~110 lines saved).
- v2.1.0 (2025-12-12): **Generation refinements** - Max 3 concepts per node per invocation.
- v2.0.0 (2025-12-11): **Breaking change** - Migrated from JSON to SQLite with closure table pattern for scalability (200-500 stories).
- v1.3.0 (2025-12-11): Added incremental commit analysis with checkpoint tracking
- v1.2.0 (2025-12-11): Added auto-update on staleness (3-day threshold)
- v1.1.0 (2025-12-11): Added autonomous mode guidance, "When NOT to Use" section
- v1.0.0 (2025-12-11): Initial release
