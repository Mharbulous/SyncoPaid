# SQL Query Reference

## Priority Algorithm - Under-Capacity Target

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
         JOIN story_nodes child ON sp.descendant_id = child.id
         WHERE sp.ancestor_id = s.id AND sp.depth = 1
         AND child.status IN ('implemented', 'ready'))) as effective_capacity
FROM story_nodes s
WHERE s.status NOT IN ('concept', 'rejected', 'deprecated', 'infeasible', 'bugged')
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
      COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
           JOIN story_nodes child ON sp.descendant_id = child.id
           WHERE sp.ancestor_id = s.id AND sp.depth = 1
           AND child.status IN ('implemented', 'ready')))
ORDER BY node_depth ASC
LIMIT 1;
```

## Insert with Closure Table Population

```sql
INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
VALUES (:new_id, :title, :description, 'concept', datetime('now'), datetime('now'));

INSERT INTO story_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, :new_id, depth + 1
FROM story_paths WHERE descendant_id = :parent_id
UNION ALL SELECT :new_id, :new_id, 0;
```

## Commit Analysis Checkpoint

```bash
LAST_COMMIT=$(python -c "import sqlite3; c=sqlite3.connect('.claude/data/story-tree.db'); print(c.execute(\"SELECT value FROM metadata WHERE key='lastAnalyzedCommit'\").fetchone()[0] or '')")

if [ -z "$LAST_COMMIT" ] || ! git cat-file -t "$LAST_COMMIT" &>/dev/null; then
    git log --since="30 days ago" --pretty=format:"%h|%ai|%s" --no-merges
else
    git log "$LAST_COMMIT"..HEAD --pretty=format:"%h|%ai|%s" --no-merges
fi
```

## Pattern Matching

### Keyword Extraction
1. Lowercase, remove special chars except hyphens
2. Split on whitespace, filter words < 3 chars
3. Filter stop words: a, an, and, are, as, at, be, by, for, from, has, he, in, is, it, its, of, on, that, the, to, was, will, with, this, but, they, have, had, what, when, where, who, which, why, how
4. Filter pure numbers, keep compound terms (e.g., "drag-and-drop")

### Similarity Thresholds (Jaccard)
- ≥ 0.7: Strong match (auto-link, update status)
- ≥ 0.4: Potential match (link, review recommended)
- < 0.4: No match

### Commit Type Detection
| Pattern | Type |
|---------|------|
| `^feat[:(]` | feature |
| `^fix[:(]` | fix |
| `^refactor[:(]` | refactor |
| `(add\|implement\|create)` | feature |
| `(fix\|bug\|issue)` | fix |
