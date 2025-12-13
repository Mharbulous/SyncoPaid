# Tree Analyzer

This document provides SQL queries for analyzing the story tree structure, calculating metrics, and identifying priority targets.

> **For tree visualization**, use `tree-view.py` instead of SQL queries:
> ```bash
> python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii
> ```
> See [Query 5](#query-5-tree-visualization-data) for SQL alternatives if needed.

## Query 1: Get All Stories with Metrics

Retrieve all stories with their depth and child count:

```sql
SELECT
    s.id,
    s.title,
    s.description,
    s.capacity,
    s.status,
    s.project_path,
    s.last_implemented,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    ROUND((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 1.0 / s.capacity, 2) as fill_rate,
    s.capacity - (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as needs_children
FROM story_nodes s
ORDER BY node_depth ASC, s.id;
```

## Query 2: Calculate Tree Statistics

### Overall Metrics

```sql
-- Total nodes by status
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM story_nodes), 1) as percentage
FROM story_nodes
GROUP BY status
ORDER BY count DESC;
```

### Nodes by Depth

```sql
-- Count nodes at each depth level
SELECT
    node_depth,
    COUNT(*) as node_count,
    SUM(capacity) as total_capacity,
    SUM(child_count) as total_children,
    ROUND(AVG(fill_rate), 2) as avg_fill_rate
FROM (
    SELECT
        s.id,
        s.capacity,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 1.0 / s.capacity as fill_rate
    FROM story_nodes s
) sub
GROUP BY node_depth
ORDER BY node_depth;
```

### Implementation Progress by Parent

```sql
-- For each node, count children by status
SELECT
    parent.id as parent_id,
    parent.title as parent_story,
    COUNT(CASE WHEN child.status = 'implemented' THEN 1 END) as implemented,
    COUNT(CASE WHEN child.status = 'in-progress' THEN 1 END) as in_progress,
    COUNT(CASE WHEN child.status = 'planned' THEN 1 END) as planned,
    COUNT(CASE WHEN child.status = 'concept' THEN 1 END) as concept,
    COUNT(CASE WHEN child.status = 'deprecated' THEN 1 END) as deprecated
FROM story_nodes parent
LEFT JOIN story_paths st ON parent.id = st.ancestor_id AND st.depth = 1
LEFT JOIN story_nodes child ON st.descendant_id = child.id
WHERE parent.id != child.id OR child.id IS NULL
GROUP BY parent.id
ORDER BY parent.id;
```

## Query 3: Identify Priority Target

The priority algorithm finds under-capacity nodes, prioritizing shallower nodes:

```sql
-- Find highest priority node for story generation
SELECT
    s.id,
    s.title,
    s.description,
    s.capacity,
    s.status,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    s.capacity - (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as needs_children,
    -- Priority score calculation
    CASE
        WHEN (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = 0 THEN 10000
        WHEN (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = 1 THEN 1000
        WHEN (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = 2 THEN 100
        WHEN (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = 3 THEN 10
        ELSE 1
    END +
    (1 - (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 1.0 / s.capacity) * 500 +
    CASE WHEN s.status IN ('implemented', 'in-progress') THEN 100 ELSE 0 END
    as priority_score
FROM story_nodes s
WHERE s.status != 'deprecated'
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) < s.capacity
ORDER BY priority_score DESC
LIMIT 1;
```

**Priority scoring:**
- Depth 0 (root): 10000 base points
- Depth 1: 1000 base points
- Depth 2: 100 base points
- Depth 3: 10 base points
- Deeper: 1 base point
- Empty bonus: up to 500 points (inversely proportional to fill rate)
- Status bonus: 100 points for implemented/in-progress nodes

## Query 4: Get Context for Story Generation

### Get Parent Node

```sql
SELECT s.* FROM story_nodes s
JOIN story_paths st ON s.id = st.ancestor_id
WHERE st.descendant_id = :node_id AND st.depth = 1;
```

### Get Sibling Nodes

```sql
-- Get siblings (same parent)
SELECT s.* FROM story_nodes s
JOIN story_paths st ON s.id = st.descendant_id
WHERE st.ancestor_id = (
    SELECT ancestor_id FROM story_paths
    WHERE descendant_id = :node_id AND depth = 1
)
AND st.depth = 1
AND s.id != :node_id;
```

### Get Existing Children

```sql
SELECT s.* FROM story_nodes s
JOIN story_paths st ON s.id = st.descendant_id
WHERE st.ancestor_id = :node_id AND st.depth = 1
ORDER BY s.id;
```

### Get Ancestors (Path from Root)

```sql
SELECT s.*, st.depth as distance_from_node
FROM story_nodes s
JOIN story_paths st ON s.id = st.ancestor_id
WHERE st.descendant_id = :node_id
ORDER BY st.depth DESC;
```

### Get Ancestor at Specific Depth

```sql
-- Get ancestor at depth N from root (for context building)
SELECT s.* FROM story_nodes s
JOIN story_paths st ON s.id = st.ancestor_id
WHERE st.descendant_id = :node_id
  AND (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = :target_depth;
```

## Query 5: Tree Visualization Data

**Preferred method:** Use `tree-view.py` for tree visualization instead of these SQL queries:
```bash
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii
```

The queries below are provided for reference and custom analysis needs.

Get data for ASCII tree rendering:

```sql
-- Recursive CTE to build tree with indentation
WITH RECURSIVE tree_view AS (
    -- Start with root
    SELECT
        s.id,
        s.title,
        s.status,
        s.capacity,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        0 as depth,
        s.id as path
    FROM story_nodes s
    WHERE s.id = 'root'

    UNION ALL

    -- Add children
    SELECT
        child.id,
        child.title,
        child.status,
        child.capacity,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = child.id AND depth = 1),
        tv.depth + 1,
        tv.path || '/' || child.id
    FROM tree_view tv
    JOIN story_paths st ON tv.id = st.ancestor_id AND st.depth = 1
    JOIN story_nodes child ON st.descendant_id = child.id
)
SELECT
    id,
    title,
    status,
    printf('[%d/%d]', child_count, capacity) as capacity_display,
    depth,
    CASE
        WHEN child_count >= capacity THEN 'at-capacity'
        WHEN child_count = 0 THEN 'empty'
        ELSE 'under-capacity'
    END as capacity_status
FROM tree_view
ORDER BY path;
```

### Generate ASCII Tree

```sql
-- Formatted tree output
SELECT
    printf('%s%s: %s [%d/%d] %s',
        substr('                    ', 1, depth * 2),
        CASE WHEN depth > 0 THEN '|- ' ELSE '' END,
        title,
        child_count,
        capacity,
        CASE
            WHEN status = 'implemented' THEN '[done]'
            WHEN status = 'in-progress' THEN '[WIP]'
            WHEN status = 'planned' THEN '[planned]'
            WHEN status = 'deprecated' THEN '[deprecated]'
            WHEN child_count < capacity THEN '<- NEEDS WORK'
            ELSE ''
        END
    ) as tree_line
FROM (
    SELECT
        s.id,
        s.title,
        s.status,
        s.capacity,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as depth
    FROM story_nodes s
    ORDER BY s.id
);
```

## Query 6: Capacity Recommendations

Find nodes that may need capacity adjustments:

```sql
-- Over-capacity nodes
SELECT
    s.id,
    s.title,
    s.capacity as current_capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as actual_children,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as suggested_capacity,
    'over-capacity' as issue
FROM story_nodes s
WHERE (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity

UNION ALL

-- Empty nodes with very high capacity
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1),
    5,
    'high-capacity-empty'
FROM story_nodes s
WHERE s.capacity > 10
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = 0

UNION ALL

-- Full implemented nodes that might need expansion
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1),
    s.capacity + 3,
    'at-capacity-implemented'
FROM story_nodes s
WHERE s.status = 'implemented'
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) >= s.capacity
  AND NOT EXISTS (
      SELECT 1 FROM story_nodes child
      JOIN story_paths st ON child.id = st.descendant_id
      WHERE st.ancestor_id = s.id AND st.depth = 1 AND child.status != 'implemented'
  );
```

## Query 7: Tree Health Metrics

Calculate overall tree health score:

```sql
-- Tree health metrics
SELECT
    -- Balance score (30 points max)
    ROUND(30 - (
        SELECT AVG((count - avg_count) * (count - avg_count))
        FROM (
            SELECT
                (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as depth,
                COUNT(*) as count
            FROM story_nodes s
            GROUP BY depth
        ) depth_counts,
        (SELECT AVG(count) as avg_count FROM (
            SELECT COUNT(*) as count FROM story_nodes GROUP BY (SELECT MIN(depth) FROM story_paths WHERE descendant_id = id)
        ))
    ) / 10, 1) as balance_score,

    -- Utilization score (30 points max)
    ROUND((
        SELECT AVG(
            (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 1.0 / s.capacity
        )
        FROM story_nodes s
    ) * 30, 1) as utilization_score,

    -- Progress score (25 points max)
    ROUND((
        SELECT COUNT(*) * 1.0 / (SELECT COUNT(*) FROM story_nodes)
        FROM story_nodes WHERE status = 'implemented'
    ) * 25, 1) as progress_score,

    -- Root coverage score (15 points max)
    ROUND(
        MIN(1.0, (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = 'root' AND depth = 1) * 1.0 /
            (SELECT capacity FROM story_nodes WHERE id = 'root')
        ) * 15, 1
    ) as coverage_score;
```

## Usage Example: Complete Analysis Workflow

```bash
#!/bin/bash
DB=".claude/data/story-tree.db"

echo "=== Story Tree Analysis ==="
echo ""

echo "1. Tree Statistics"
sqlite3 $DB "
SELECT status, COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM story_nodes), 1) as pct
FROM story_nodes GROUP BY status ORDER BY count DESC;
"

echo ""
echo "2. Priority Target"
sqlite3 $DB "
SELECT id, title, child_count || '/' || capacity as capacity
FROM (
    SELECT s.id, s.title, s.capacity,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.status != 'deprecated'
      AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) < s.capacity
    ORDER BY node_depth ASC,
        (child_count * 1.0 / s.capacity) ASC
    LIMIT 1
);
"

echo ""
echo "3. Tree Structure"
sqlite3 $DB "
SELECT printf('%s%s [%d/%d]',
    substr('    ', 1, depth * 2),
    title, child_count, capacity)
FROM (
    SELECT s.title, s.capacity,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as depth
    FROM story_nodes s ORDER BY s.id
);
"
```

## Version History

- v2.0.0 (2025-12-11): Rewritten for SQLite with closure table pattern. All JavaScript functions replaced with SQL queries.
- v1.0.0 (2025-12-11): Initial release with JavaScript-based tree traversal
