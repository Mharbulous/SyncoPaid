# Capacity Management

This document provides detailed guidance on handling capacity-related issues in the story tree using SQL queries, including over-capacity violations and capacity adjustments.

## Database Connection

All queries use the SQLite database at `.claude/data/story-tree.db`.

```bash
sqlite3 .claude/data/story-tree.db
```

## Handling Over-Capacity Nodes

**Over-capacity** = node has more children than its capacity allows (e.g., capacity 3 but 4 children exist).

### Query 1: Detect Over-Capacity Nodes

```sql
-- Find all over-capacity nodes
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as actual_children,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) - s.capacity as excess
FROM story_nodes s
WHERE (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity
ORDER BY excess DESC;
```

### Report Over-Capacity Issues

When over-capacity is detected, include in the analysis section:

```markdown
## Over-Capacity Violations Detected

**Node 1.1 'Product catalog' is OVER-CAPACITY:**
- Target capacity: 3 children
- Actual children: 4
- Over by: 1 child

**Children:**
[list children from query below]
```

### Query 2: Get Children of Over-Capacity Node

```sql
-- Get children of a specific node
SELECT s.id, s.title, s.status
FROM story_nodes s
JOIN story_paths st ON s.id = st.descendant_id
WHERE st.ancestor_id = :node_id AND st.depth = 1
ORDER BY s.id;
```

### Resolution Options

Over-capacity is a **product decision**, not a bug. Provide options to the user:

```markdown
**Options to resolve:**

1. **Increase capacity** - If all children are valuable:
   - Command: `Set capacity for 1.1 to 4`
   - SQL: `UPDATE story_nodes SET capacity = 4 WHERE id = '1.1';`

2. **Deprecate low-priority story** - If one is no longer relevant:
   - Command: `Mark 1.1.4 as deprecated`
   - SQL: `UPDATE story_nodes SET status = 'deprecated' WHERE id = '1.1.4';`

3. **Merge overlapping stories** - If two stories are redundant:
   - Identify stories with similar descriptions
   - Combine into single story

**My recommendation**: [Analysis-based suggestion]
```

### What NOT to Do

**Do NOT**:
- Automatically increase capacity
- Automatically deprecate stories
- Skip the node and continue silently
- Delete child nodes without user consent

---

## Capacity Queries

### Query 3: Get Capacity Status for All Nodes

```sql
-- Complete capacity status for all nodes
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children,
    CASE
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity THEN 'OVER'
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = s.capacity THEN 'AT'
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) >= s.capacity * 0.7 THEN 'NEAR'
        ELSE 'UNDER'
    END as status,
    s.capacity - (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as remaining
FROM story_nodes s
ORDER BY
    CASE
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity THEN 1
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = s.capacity THEN 2
        ELSE 3
    END,
    s.id;
```

### Query 4: Capacity Summary by Level

```sql
-- Capacity summary grouped by depth level
SELECT
    node_depth as level,
    COUNT(*) as node_count,
    SUM(capacity) as total_capacity,
    SUM(children) as total_children,
    ROUND(SUM(children) * 100.0 / SUM(capacity), 1) as fill_pct,
    SUM(CASE WHEN children > capacity THEN 1 ELSE 0 END) as over_capacity,
    SUM(CASE WHEN children < capacity THEN 1 ELSE 0 END) as under_capacity
FROM (
    SELECT
        s.id,
        s.capacity,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children
    FROM story_nodes s
) sub
GROUP BY node_depth
ORDER BY node_depth;
```

---

## Capacity Recommendations

### Query 5: Generate Capacity Recommendations

```sql
-- Nodes that may need capacity adjustments
SELECT
    s.id,
    s.title,
    s.capacity as current_capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as actual_children,
    CASE
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity
            THEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1)
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = 0 AND s.capacity > 10
            THEN 5
        WHEN s.status = 'implemented'
            AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) >= s.capacity
            THEN s.capacity + 3
        ELSE NULL
    END as suggested_capacity,
    CASE
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity
            THEN 'over-capacity: increase to match children'
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = 0 AND s.capacity > 10
            THEN 'high-capacity-empty: start smaller'
        WHEN s.status = 'implemented'
            AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) >= s.capacity
            THEN 'at-capacity-implemented: allow expansion'
        ELSE NULL
    END as reason
FROM story_nodes s
WHERE
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity
    OR ((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) = 0 AND s.capacity > 10)
    OR (s.status = 'implemented'
        AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) >= s.capacity);
```

### Recommendation Rules

1. **Node is over-capacity**: Suggest increasing to current children count
2. **All children implemented and at capacity**: Suggest expansion for future growth
3. **Empty node with very high capacity**: Suggest starting smaller

---

## Capacity Changes

### Query 6: Update Node Capacity

```sql
-- Update capacity for a specific node
UPDATE story_nodes
SET capacity = :new_capacity, updated_at = datetime('now')
WHERE id = :node_id;
```

### Query 7: Validate Capacity Change

Before decreasing capacity, check if it would cause over-capacity:

```sql
-- Check if new capacity would be valid
SELECT
    s.id,
    s.title,
    s.capacity as current_capacity,
    :new_capacity as proposed_capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as actual_children,
    CASE
        WHEN (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > :new_capacity
            THEN 'INVALID: Would cause over-capacity'
        ELSE 'VALID'
    END as validation_result
FROM story_nodes s
WHERE s.id = :node_id;
```

### Query 8: Post-Update Verification

```sql
-- Verify capacity change and show new status
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children,
    ROUND((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 100.0 / s.capacity, 1) as fill_pct,
    s.capacity - (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as needs_children
FROM story_nodes s
WHERE s.id = :node_id;
```

---

## Capacity Estimation Guidelines

When generating new stories, estimate capacity based on complexity:

### By Story Type

| Story Type | Typical Capacity | Reasoning |
|------------|-----------------|-----------|
| **Simple UI component** | 2-3 | Single component, few props |
| **Feature with workflow** | 5-8 | Multiple components, state, API |
| **Major feature area** | 8-12 | End-to-end, integrations |
| **Cross-cutting concern** | 10-15 | Affects many areas |

### Query 9: Calibrate from Similar Stories

```sql
-- Find implemented stories at same depth level to calibrate capacity estimates
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as actual_children,
    ROUND((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) * 1.0 / s.capacity, 2) as utilization
FROM story_nodes s
WHERE s.status = 'implemented'
  AND (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) = :target_depth
ORDER BY s.id;
```

---

## Capacity Warning Messages

### Warning: Cannot Decrease Below Children

```markdown
Cannot decrease capacity to {new_value} - node already has {children} children.

Options:
1. Deprecate {excess} children first, then decrease capacity
2. Keep capacity at current level ({children})
```

### Warning: Over-Capacity Detected

```markdown
Node {id} '{story}' is over-capacity:
- Current capacity: {capacity}
- Actual children: {children}
- Over by: {excess}

This should be resolved before generating new stories.
```

---

## Example Workflow

```bash
#!/bin/bash
DB=".claude/data/story-tree.db"

echo "=== Capacity Analysis ==="

# 1. Check for over-capacity
echo ""
echo "Over-capacity nodes:"
sqlite3 $DB "
SELECT s.id, s.title, s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children
FROM story_nodes s
WHERE (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity;
"

# 2. Capacity summary by level
echo ""
echo "Capacity by level:"
sqlite3 $DB -column -header "
SELECT
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as level,
    COUNT(*) as nodes,
    SUM((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1)) as children,
    SUM(s.capacity) as capacity,
    ROUND(SUM((SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1)) * 100.0 / SUM(s.capacity), 1) as fill_pct
FROM story_nodes s
GROUP BY level;
"

# 3. Recommendations
echo ""
echo "Capacity recommendations:"
sqlite3 $DB "
SELECT s.id, s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children,
    'increase to match' as suggestion
FROM story_nodes s
WHERE (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) > s.capacity;
"
```

---

## Version History

- v2.0.0 (2025-12-11): Rewritten for SQLite with SQL queries replacing JavaScript functions.
- v1.0.0 (2025-12-11): Initial documentation extracted from main SKILL.md
