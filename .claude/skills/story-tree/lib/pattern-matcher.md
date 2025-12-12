# Pattern Matcher

This document provides algorithms for matching git commits to user stories in the SQLite database, detecting implementation patterns, and updating story status based on commit history.

## Incremental Commit Analysis

### Get Commits to Analyze

```bash
# Get last analyzed commit from metadata
LAST_COMMIT=$(sqlite3 .claude/data/story-tree.db "SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit';")

if [ -z "$LAST_COMMIT" ]; then
    # No checkpoint - do full 30-day scan
    echo "Mode: Full scan (no checkpoint)"
    git log --since="30 days ago" --pretty=format:"%h|%ai|%s|%b" --no-merges
else
    # Validate checkpoint still exists
    if git cat-file -t "$LAST_COMMIT" &>/dev/null; then
        echo "Mode: Incremental from $LAST_COMMIT"
        git log "$LAST_COMMIT"..HEAD --pretty=format:"%h|%ai|%s|%b" --no-merges
    else
        echo "Mode: Full scan (checkpoint $LAST_COMMIT no longer exists)"
        git log --since="30 days ago" --pretty=format:"%h|%ai|%s|%b" --no-merges
    fi
fi
```

### Update Checkpoint After Analysis

```sql
-- After processing commits, update checkpoint to newest commit hash
INSERT OR REPLACE INTO metadata (key, value)
VALUES ('lastAnalyzedCommit', :newest_commit_hash);
```

### Analysis Mode Comparison

| Mode | Trigger | Typical Commit Count |
|------|---------|---------------------|
| Incremental | Checkpoint exists and valid | ~5-10 commits |
| Full scan | Missing checkpoint | ~150 commits |
| Full scan | Checkpoint rebased away | ~150 commits |
| Full scan | User requests "Rebuild" | ~150 commits |

**Token savings**: ~90% reduction for typical daily use.

## Keyword Extraction

Extract meaningful keywords from text for similarity matching.

### Stop Words to Filter

```
a, an, and, are, as, at, be, by, for, from, has, he, in, is, it, its, of, on,
that, the, to, was, will, with, this, but, they, have, had, what, when, where,
who, which, why, how
```

### Extraction Rules

1. Convert to lowercase
2. Remove special characters except hyphens
3. Split on whitespace
4. Filter words < 3 characters
5. Filter stop words
6. Filter pure numbers
7. Extract compound terms (e.g., "drag-and-drop" stays intact)

## Commit Type Detection

Detect commit type from subject line:

| Pattern | Type |
|---------|------|
| `^feat[:(]` | feature |
| `^fix[:(]` | fix |
| `^refactor[:(]` | refactor |
| `^docs[:(]` | docs |
| `^test[:(]` | test |
| `^chore[:(]` | chore |
| `(add\|implement\|create)` | feature |
| `(fix\|bug\|issue)` | fix |
| `(update\|improve\|refactor)` | refactor |
| Other | other |

## SQL Operations for Commit Matching

### Query 1: Get All Stories for Matching

```sql
-- Get stories that could potentially match commits
SELECT
    s.id,
    s.title,
    s.description,
    s.status,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as depth
FROM story_nodes s
WHERE s.status NOT IN ('deprecated', 'active')
ORDER BY s.id;
```

### Query 2: Check if Commit Already Linked

```sql
-- Check if commit is already linked to any story
SELECT story_id FROM story_commits WHERE commit_hash = :commit_hash;
```

### Query 3: Link Commit to Story

```sql
-- Insert commit link
INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
VALUES (:story_id, :commit_hash, :commit_date, :commit_message);
```

### Query 4: Update Story Status

```sql
-- Update story status when commits match
-- From concept/planned/in-progress to implemented
UPDATE story_nodes
SET
    status = CASE
        WHEN status IN ('planned', 'in-progress') THEN 'implemented'
        WHEN status = 'concept' THEN 'in-progress'
        ELSE status
    END,
    last_implemented = :commit_date,
    updated_at = datetime('now')
WHERE id = :story_id
  AND status IN ('concept', 'planned', 'in-progress');
```

### Query 5: Get Story Commits

```sql
-- Get all commits linked to a story
SELECT commit_hash, commit_date, commit_message
FROM story_commits
WHERE story_id = :story_id
ORDER BY commit_date DESC;
```

### Query 6: Get Stories with Commit Counts

```sql
-- Get stories with their linked commit counts
SELECT
    s.id,
    s.title,
    s.status,
    COUNT(sc.commit_hash) as commit_count,
    MAX(sc.commit_date) as latest_commit
FROM story_nodes s
LEFT JOIN story_commits sc ON s.id = sc.story_id
GROUP BY s.id
ORDER BY commit_count DESC;
```

## Pattern Detection Queries

### Query 7: Feature Focus Detection

Find features with heavy recent commit activity:

```sql
-- Get keywords that appear frequently in recent commits
-- (Run this after extracting keywords from commits)
SELECT
    s.id,
    s.title,
    COUNT(sc.commit_hash) as commit_count
FROM story_nodes s
JOIN story_commits sc ON s.id = sc.story_id
WHERE sc.commit_date > date('now', '-7 days')
GROUP BY s.id
HAVING commit_count >= 3
ORDER BY commit_count DESC;
```

### Query 8: Bug Cluster Detection

Find stories with multiple bug fix commits:

```sql
-- Stories with multiple fix-type commits (check commit_message for 'fix:' prefix)
SELECT
    s.id,
    s.title,
    COUNT(sc.commit_hash) as fix_count
FROM story_nodes s
JOIN story_commits sc ON s.id = sc.story_id
WHERE sc.commit_message LIKE 'fix:%'
   OR sc.commit_message LIKE '%fix %'
   OR sc.commit_message LIKE '%bug%'
GROUP BY s.id
HAVING fix_count >= 2
ORDER BY fix_count DESC;
```

### Query 9: Orphaned Stories

Find implemented stories without commits:

```sql
-- Stories marked implemented but no commits linked
SELECT s.id, s.title, s.status
FROM story_nodes s
WHERE s.status = 'implemented'
  AND NOT EXISTS (
      SELECT 1 FROM story_commits sc WHERE sc.story_id = s.id
  );
```

### Query 10: In-Progress Stories with Many Commits

```sql
-- Stories that might be ready to mark as implemented
SELECT
    s.id,
    s.title,
    s.status,
    COUNT(sc.commit_hash) as commit_count,
    MAX(sc.commit_date) as latest_commit
FROM story_nodes s
JOIN story_commits sc ON s.id = sc.story_id
WHERE s.status = 'in-progress'
GROUP BY s.id
HAVING commit_count >= 3
  AND latest_commit > date('now', '-7 days')
ORDER BY commit_count DESC;
```

## Gap Analysis Queries

### Query 11: Under-Detailed Implemented Stories

```sql
-- Implemented stories with few children (might need more detail)
SELECT
    s.id,
    s.title,
    s.capacity,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
FROM story_nodes s
WHERE s.status = 'implemented'
  AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) < s.capacity * 0.5
ORDER BY child_count ASC;
```

### Query 12: Missing Quality Stories

Stories with bug clusters but no testing/error handling children:

```sql
-- Stories that have bugs but lack quality-focused children
SELECT
    s.id,
    s.title,
    COUNT(sc.commit_hash) as fix_count
FROM story_nodes s
JOIN story_commits sc ON s.id = sc.story_id
WHERE (sc.commit_message LIKE 'fix:%' OR sc.commit_message LIKE '%bug%')
  AND NOT EXISTS (
      SELECT 1 FROM story_nodes child
      JOIN story_paths st ON child.id = st.descendant_id
      WHERE st.ancestor_id = s.id
        AND st.depth = 1
        AND (child.description LIKE '%test%'
             OR child.description LIKE '%error%'
             OR child.description LIKE '%validat%')
  )
GROUP BY s.id
HAVING fix_count >= 2;
```

## Matching Algorithm Workflow

### Step 1: Parse Git Log Output

```bash
# Get commits in parseable format
git log $LAST_COMMIT..HEAD --pretty=format:"%h|%ai|%s" --no-merges
```

Output format: `hash|date|subject`

### Step 2: For Each Commit

1. Extract keywords from commit message
2. Detect commit type (feature/fix/refactor/etc.)
3. Query all non-deprecated stories
4. For each story:
   - Extract keywords from story description
   - Calculate Jaccard similarity
   - If similarity >= 0.4, consider a potential match
   - If similarity >= 0.7, consider a strong match

### Step 3: Process Matches

```sql
-- Insert match (high confidence)
INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
VALUES (:story_id, :commit_hash, :commit_date, :commit_message);

-- Update status if appropriate
UPDATE story_nodes
SET status = 'implemented',
    last_implemented = :commit_date,
    updated_at = datetime('now')
WHERE id = :story_id
  AND status IN ('planned', 'in-progress');
```

### Step 4: Update Checkpoint

```sql
INSERT OR REPLACE INTO metadata (key, value)
VALUES ('lastAnalyzedCommit', :newest_commit_hash);

INSERT OR REPLACE INTO metadata (key, value)
VALUES ('lastUpdated', datetime('now'));
```

## Similarity Thresholds

Calculate Jaccard similarity between keyword sets:
- >= 0.7: Strong match (auto-link, update status)
- >= 0.4: Potential match (link, review recommended)
- < 0.4: No match

## Example Workflow

```bash
#!/bin/bash
DB=".claude/data/story-tree.db"

# 1. Get checkpoint
LAST=$(sqlite3 $DB "SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit';")

# 2. Get commits to analyze
if [ -z "$LAST" ]; then
    COMMITS=$(git log --since="30 days ago" --pretty=format:"%h|%ai|%s" --no-merges)
else
    COMMITS=$(git log "$LAST"..HEAD --pretty=format:"%h|%ai|%s" --no-merges 2>/dev/null || \
              git log --since="30 days ago" --pretty=format:"%h|%ai|%s" --no-merges)
fi

# 3. Check if any commits
if [ -z "$COMMITS" ]; then
    echo "No new commits to analyze"
    exit 0
fi

# 4. Get stories for matching
STORIES=$(sqlite3 $DB "SELECT id, description FROM story_nodes WHERE status NOT IN ('deprecated', 'active');")

# 5. Process matches (logic implemented in skill)
# ... keyword extraction and matching ...

# 6. Update checkpoint
NEWEST=$(echo "$COMMITS" | head -1 | cut -d'|' -f1)
sqlite3 $DB "INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', '$NEWEST');"
sqlite3 $DB "INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'));"
```

## Version History

- v2.0.0 (2025-12-11): Rewritten for SQLite storage. Commit tracking now uses `story_commits` table instead of JSON arrays.
- v1.0.0 (2025-12-11): Initial release with JSON-based commit tracking
