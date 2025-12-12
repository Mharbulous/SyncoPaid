# Closure Table Concept

The `story_paths` table stores ALL ancestor-descendant pairs, not just parent-child relationships. This enables efficient subtree queries without recursion.

## Example

For this tree structure:
```
root → 1.1 → 1.1.1
```

The `story_paths` table contains:

| ancestor_id | descendant_id | depth |
|-------------|---------------|-------|
| root        | root          | 0     | (self-reference)
| root        | 1.1           | 1     | (root's child)
| root        | 1.1.1         | 2     | (root's grandchild)
| 1.1         | 1.1           | 0     | (self-reference)
| 1.1         | 1.1.1         | 1     | (1.1's child)
| 1.1.1       | 1.1.1         | 0     | (self-reference)

## Key Benefits

1. **No recursion needed** - Get entire subtree with single query
2. **Efficient depth queries** - Filter by `depth` column
3. **Easy ancestor lookup** - Find all ancestors of any node
4. **Simple insertions** - Copy ancestor paths + add self-reference

## Common Queries

```sql
-- Get all descendants of a node
SELECT descendant_id FROM story_paths WHERE ancestor_id = 'root' AND depth > 0;

-- Get all ancestors of a node
SELECT ancestor_id FROM story_paths WHERE descendant_id = '1.1.1' AND depth > 0;

-- Get direct children only
SELECT descendant_id FROM story_paths WHERE ancestor_id = 'root' AND depth = 1;

-- Get node's depth in tree
SELECT MIN(depth) FROM story_paths WHERE descendant_id = '1.1.1';
```
