# Story Tree Structure Documentation

This document provides comprehensive documentation of the story tree SQLite schema, table definitions, field constraints, and best practices.

## Database Overview

The story tree uses SQLite with a **closure table pattern** for efficient hierarchical data storage and queries.

**Database location:** `.claude/data/story-tree.db`

**Why this location:** The skill definition files (in `.claude/skills/story-tree/`) are meant to be copied between projects. The database contains project-specific data and lives separately in `.claude/data/` so it's never accidentally copied or overwritten.

**Schema file:** `.claude/skills/story-tree/schema.sql`

## Why Closure Table Pattern?

The closure table pattern stores ALL ancestor-descendant relationships, not just parent-child:

**Advantages:**
- Get entire subtree in single query (no recursion)
- Get all ancestors in single query
- O(1) depth calculation
- Efficient for read-heavy workloads

**Trade-offs:**
- More storage (O(n*depth) rows in closure table)
- Insert requires populating closure relationships
- Delete cascades through closure table

**Comparison with alternatives:**

| Pattern | Read Performance | Write Performance | Query Complexity |
|---------|-----------------|-------------------|------------------|
| Closure Table | Excellent | Good | Simple |
| Adjacency List | Poor (recursive) | Excellent | Complex (CTEs) |
| Nested Sets | Excellent | Poor | Moderate |
| Materialized Path | Good | Good | Moderate |

## Table Definitions

### Table 1: `story_nodes`

Main table storing all story data.

```sql
CREATE TABLE story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN ('concept','planned','in-progress','implemented','deprecated','active')),
    project_path TEXT,
    last_implemented TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | TEXT | Yes | Unique hierarchical identifier (e.g., "root", "1.1", "1.3.2") |
| `title` | TEXT | Yes | Short title (3-100 chars recommended) |
| `description` | TEXT | Yes | Full user story in "As a... I want... So that..." format |
| `capacity` | INTEGER | Yes | Target number of child nodes (0-20 recommended) |
| `status` | TEXT | Yes | Current implementation status |
| `project_path` | TEXT | No | Relative path for multi-project support |
| `last_implemented` | TEXT | No | ISO 8601 timestamp of last implementation |
| `created_at` | TEXT | Yes | ISO 8601 creation timestamp |
| `updated_at` | TEXT | Yes | ISO 8601 last update timestamp |

#### Status Values

| Status | Description | Can Transition To |
|--------|-------------|-------------------|
| `concept` | Idea exists, not approved | planned, deprecated |
| `planned` | Approved for development | in-progress, deprecated |
| `in-progress` | Currently being implemented | implemented, deprecated |
| `implemented` | Complete and working | deprecated |
| `deprecated` | No longer relevant | (terminal) |
| `active` | Root node only | (special) |

#### ID Format Rules

- **Root**: `"root"` (exactly)
- **Level 1**: `"1.1"`, `"1.2"`, etc.
- **Level 2+**: Parent ID + `.` + sequence number
- **Examples**: `"1.1"`, `"1.3.2"`, `"1.3.2.1"`

### Table 2: `story_paths`

Closure table storing ALL ancestor-descendant relationships.

```sql
CREATE TABLE story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ancestor_id` | TEXT | Yes | ID of ancestor node |
| `descendant_id` | TEXT | Yes | ID of descendant node |
| `depth` | INTEGER | Yes | Distance between ancestor and descendant (0 = self) |

#### Closure Table Example

For a tree: `root → 1.1 → 1.1.1`

| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root | root | 0 |
| root | 1.1 | 1 |
| root | 1.1.1 | 2 |
| 1.1 | 1.1 | 0 |
| 1.1 | 1.1.1 | 1 |
| 1.1.1 | 1.1.1 | 0 |

**Key insight:** Every node has a self-reference (depth=0).

### Table 3: `story_commits`

Links git commits to stories for implementation tracking.

```sql
CREATE TABLE story_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `story_id` | TEXT | Yes | ID of related story |
| `commit_hash` | TEXT | Yes | Git commit hash (short or full) |
| `commit_date` | TEXT | No | ISO 8601 commit timestamp |
| `commit_message` | TEXT | No | Commit subject line |

### Table 4: `metadata`

Key-value storage for tree-level metadata.

```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

#### Standard Keys

| Key | Description | Example Value |
|-----|-------------|---------------|
| `version` | Schema version | `"2.0.0"` |
| `lastUpdated` | Last tree update | `"2025-12-11T14:32:00"` |
| `lastAnalyzedCommit` | Checkpoint for incremental analysis | `"a1b2c3d"` |

## Indexes

```sql
CREATE INDEX idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX idx_paths_depth ON story_paths(depth);
CREATE INDEX idx_story_nodes_status ON story_nodes(status);
CREATE INDEX idx_commits_hash ON story_commits(commit_hash);
```

**Index purposes:**
- `idx_paths_descendant`: Fast ancestor lookups
- `idx_paths_depth`: Fast direct children queries (depth=1)
- `idx_story_nodes_status`: Fast status filtering
- `idx_commits_hash`: Fast commit lookups

## Common Operations

### Insert New Node

```sql
-- Step 1: Insert story
INSERT INTO story_nodes (id, title, description, capacity, status, created_at, updated_at)
VALUES (:new_id, :title, :description, :capacity, 'concept', datetime('now'), datetime('now'));

-- Step 2: Populate closure table
INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, :new_id, depth + 1
FROM story_paths WHERE descendant_id = :parent_id
UNION ALL SELECT :new_id, :new_id, 0;
```

### Get Direct Children

```sql
SELECT s.* FROM story_nodes s
JOIN story_paths st ON s.id = st.descendant_id
WHERE st.ancestor_id = :parent_id AND st.depth = 1
ORDER BY s.id;
```

### Get Entire Subtree

```sql
SELECT s.*, st.depth as relative_depth FROM story_nodes s
JOIN story_paths st ON s.id = st.descendant_id
WHERE st.ancestor_id = :root_id
ORDER BY st.depth, s.id;
```

### Get All Ancestors (Path to Root)

```sql
SELECT s.*, st.depth as distance FROM story_nodes s
JOIN story_paths st ON s.id = st.ancestor_id
WHERE st.descendant_id = :node_id
ORDER BY st.depth DESC;
```

### Get Node Depth

```sql
SELECT MIN(depth) as node_depth
FROM story_paths
WHERE descendant_id = :node_id;
```

### Delete Node and Descendants

```sql
-- CASCADE handles story_paths cleanup automatically
DELETE FROM story_nodes WHERE id IN (
    SELECT descendant_id FROM story_paths WHERE ancestor_id = :node_id
);
```

### Update Node Status

```sql
UPDATE story_nodes
SET status = :new_status, updated_at = datetime('now')
WHERE id = :node_id;
```

## Validation Rules

### Structural Validation

```sql
-- Check for orphaned nodes (no self-reference)
SELECT s.id, s.title FROM story_nodes s
WHERE NOT EXISTS (
    SELECT 1 FROM story_paths st
    WHERE st.ancestor_id = s.id AND st.descendant_id = s.id AND st.depth = 0
);

-- Check for duplicate IDs (should never happen with PRIMARY KEY)
SELECT id, COUNT(*) FROM story_nodes GROUP BY id HAVING COUNT(*) > 1;

-- Check for invalid status values
SELECT id, status FROM story_nodes
WHERE status NOT IN ('concept', 'planned', 'in-progress', 'implemented', 'deprecated', 'active');

-- Verify root node exists and has 'active' status
SELECT CASE
    WHEN (SELECT COUNT(*) FROM story_nodes WHERE id = 'root' AND status = 'active') = 1
    THEN 'OK'
    ELSE 'MISSING ROOT'
END as root_check;
```

### Semantic Validation

```sql
-- Implemented stories without commits
SELECT id, title FROM story_nodes
WHERE status = 'implemented'
  AND NOT EXISTS (SELECT 1 FROM story_commits WHERE story_id = id);

-- In-progress stories with many commits (might be implemented)
SELECT s.id, s.title, COUNT(sc.commit_hash) as commits
FROM story_nodes s
JOIN story_commits sc ON s.id = sc.story_id
WHERE s.status = 'in-progress'
GROUP BY s.id
HAVING commits > 3;

-- Over-capacity nodes
SELECT s.id, s.title, s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children
FROM story_nodes s
WHERE (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity;
```

## Best Practices

### Story Writing

**Good format:**
```
title: "Bulk document categorization"
description: "As a legal assistant, I want to categorize multiple documents at once so that I can organize case files efficiently"
```

**Poor format:**
```
title: "Improve UX"
description: "Make it better"
```

### Capacity Guidelines

| Node Depth | Typical Capacity | Notes |
|------------|-----------------|-------|
| 0 (root) | 5-10 | Major product areas |
| 1 (apps) | 5-10 | Major feature areas |
| 2 (features) | 3-8 | Specific capabilities |
| 3+ (details) | 2-4 | Implementation details |

### Status Management

- **Don't rush to "implemented"**: Only when feature is complete and working
- **Use "concept" liberally**: Brainstorm freely, promote when approved
- **Mark deprecated, don't delete**: Preserves history and rationale

## Migration from JSON

If you have an existing `story-tree.json` file in the skill folder, see `docs/migration-guide.md` for migration instructions. The JSON file will be migrated to `.claude/data/story-tree.db`.

## Schema Diagram

```
┌─────────────────────────────────────────────────┐
│ story_nodes                                      │
├─────────────────────────────────────────────────┤
│ PK id TEXT                                       │
│    title TEXT NOT NULL                           │
│    description TEXT NOT NULL                     │
│    capacity INTEGER NOT NULL                     │
│    status TEXT NOT NULL (CHECK constraint)       │
│    project_path TEXT                             │
│    last_implemented TEXT                         │
│    created_at TEXT NOT NULL                      │
│    updated_at TEXT NOT NULL                      │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ story_paths    │ │ story_commits │ │ metadata      │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ FK ancestor_id│ │ FK story_id   │ │ PK key TEXT   │
│ FK descendant │ │ PK commit_hash│ │    value TEXT │
│    depth INT  │ │    commit_date│ └───────────────┘
│ PK(anc,desc)  │ │    message    │
└───────────────┘ └───────────────┘
```

## Version History

- v2.0.0 (2025-12-11): Complete rewrite for SQLite with closure table pattern. Replaces JSON schema documentation.
- v1.0.0 (2025-12-11): Initial JSON schema documentation
