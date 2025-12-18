# SQL Query Reference (Three-Field System v4.0)

## Priority Algorithm - Under-Capacity Target

```sql
SELECT s.*,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
         JOIN story_nodes child ON sp.descendant_id = child.id
         WHERE sp.ancestor_id = s.id AND sp.depth = 1
         AND child.stage IN ('implemented', 'ready', 'released')
         AND child.disposition IS NULL)) as effective_capacity
FROM story_nodes s
WHERE s.stage != 'concept'
  AND s.hold_reason IS NULL
  AND s.disposition IS NULL
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
      COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
           JOIN story_nodes child ON sp.descendant_id = child.id
           WHERE sp.ancestor_id = s.id AND sp.depth = 1
           AND child.stage IN ('implemented', 'ready', 'released')
           AND child.disposition IS NULL))
ORDER BY node_depth ASC
LIMIT 1;
```

## Insert with Closure Table Population

```sql
INSERT INTO story_nodes (id, title, description, stage, created_at, updated_at)
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

## Three-Field Query Patterns

### Active Pipeline (not held, not disposed)
```sql
SELECT * FROM story_nodes
WHERE disposition IS NULL AND hold_reason IS NULL
ORDER BY stage;
```

### Stories Needing Human Review
```sql
SELECT * FROM story_nodes WHERE human_review = 1;
```

### What's Held (and where to resume)
```sql
SELECT id, title, stage, hold_reason, notes FROM story_nodes
WHERE hold_reason IS NOT NULL;
```

### Ready to Plan (approved, not held)
```sql
SELECT * FROM story_nodes
WHERE stage = 'approved' AND hold_reason IS NULL AND disposition IS NULL;
```

### Ready to Execute (planned, not held)
```sql
SELECT * FROM story_nodes
WHERE stage = 'planned'
  AND hold_reason IS NULL AND disposition IS NULL
ORDER BY updated_at ASC;
```

### Check Dependencies Before Execution
```sql
-- Check if all children are at least planned (required before execution)
SELECT s.id, s.title, s.stage FROM story_nodes s
JOIN story_paths p ON s.id = p.descendant_id
WHERE p.ancestor_id = ? AND p.depth = 1
  AND s.disposition IS NULL
  AND s.stage NOT IN ('planned', 'active', 'reviewing',
                       'verifying', 'implemented', 'ready', 'polish', 'released');

-- If dependencies not met, block the story:
UPDATE story_nodes
SET hold_reason = 'blocked', human_review = 1,
    notes = COALESCE(notes || char(10), '') || 'BLOCKED - Dependencies not met: ' || datetime('now')
WHERE id = ? AND stage = 'planned';
```

### Update to Hold (preserves stage)
```sql
UPDATE story_nodes
SET hold_reason = 'pending', human_review = 1,
    notes = COALESCE(notes || char(10), '') || 'Reason: ...'
WHERE id = ?;
```

### Clear Hold (resume from preserved stage)
```sql
UPDATE story_nodes
SET hold_reason = NULL, human_review = 0
WHERE id = ?;
```

### Set Disposition (terminal)
```sql
UPDATE story_nodes
SET disposition = 'rejected', human_review = 0
WHERE id = ?;
```

### Pipeline Stage Counts
```sql
SELECT stage, COUNT(*) as cnt FROM story_nodes
WHERE disposition IS NULL
GROUP BY stage ORDER BY
  CASE stage
    WHEN 'concept' THEN 1 WHEN 'approved' THEN 2 WHEN 'planned' THEN 3
    WHEN 'active' THEN 4 WHEN 'reviewing' THEN 5 WHEN 'verifying' THEN 6
    WHEN 'implemented' THEN 7 WHEN 'ready' THEN 8 WHEN 'polish' THEN 9
    WHEN 'released' THEN 10
  END;
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
