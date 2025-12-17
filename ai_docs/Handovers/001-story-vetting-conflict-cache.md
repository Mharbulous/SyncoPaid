# Handover: Story Vetting Conflict Classification Cache

## Objective

Add persistent caching to story-vetting skill to avoid repeatedly running expensive LLM classifications on the same story pairs daily.

## Problem Statement

The story-vetting skill runs in two phases:
1. **Phase 1 (cheap)**: Heuristics flag potential conflicts using keyword/similarity matching
2. **Phase 2 (expensive)**: LLM classifies each candidate as duplicate/overlap/competing/incompatible/false_positive

Current issue: With 77 stories, Phase 1 generates **238 candidate pairs**. When run daily, the same pairs get re-analyzed repeatedly, wasting tokens.

## Background: Entity Resolution

This problem is a well-studied domain called **Entity Resolution** (also: record linkage, deduplication). The standard workflow is:

```
Indexing/Blocking → Comparison → Classification
```

### How Our System Maps to Standard Terms

| Component | Standard Term | Our Implementation |
|-----------|--------------|---------------------|
| Phase 1 heuristics | **Blocking/Indexing** | Reduces 2,926 pairs → 238 candidates |
| LLM classification | **Classification** | Determines conflict type |
| Avoiding re-work | **Incremental Linkage** | **Missing - this is what we're adding** |

### Key Insight

The standard approach to avoiding O(N²) comparisons is **blocking** - grouping records by shared attributes. Our Phase 1 already does this. The missing piece is **incremental linkage**: only re-processing pairs when the underlying data changes.

### References

- [ACM Survey: Blocking and Filtering Techniques for Entity Resolution](https://dl.acm.org/doi/abs/10.1145/3377455)
- [Python Record Linkage Toolkit](https://recordlinkage.readthedocs.io/en/latest/about.html)
- [ScienceDirect: Incremental Record Linkage Heuristics](https://www.sciencedirect.com/science/article/abs/pii/S0164121217302972)

---

## Solution: Hybrid Cache + Version Tracking

### Why Hybrid?

1. **Cache robustness**: If vetting is interrupted mid-run, cached decisions preserve progress
2. **Bootstrapping**: Existing 77 stories lack creation timestamps - cache pays off immediately on run #2
3. **Version tracking**: Simple integer increment detects changes without complex hash computation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Phase 1: Blocking                        │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │ All Stories │───▶│  Heuristics  │───▶│ Candidate Pairs   │  │
│  │   (N=77)    │    │  (blocking)  │    │     (~238)        │  │
│  └─────────────┘    └──────────────┘    └─────────┬─────────┘  │
└───────────────────────────────────────────────────┼─────────────┘
                                                    │
                    ┌───────────────────────────────▼─────────────┐
                    │           Cache Lookup                      │
                    │  ┌─────────────────────────────────────┐   │
                    │  │ For each candidate:                 │   │
                    │  │   - Check vetting_decisions table   │   │
                    │  │   - Compare story versions          │   │
                    │  │   - Skip if cached & versions match │   │
                    │  └─────────────────────────────────────┘   │
                    └───────────────────────────────┬─────────────┘
                                                    │
                    ┌───────────────────────────────▼─────────────┐
                    │         Phase 2: Classification             │
                    │  ┌─────────────────────────────────────┐   │
                    │  │ Only uncached/invalidated pairs:    │   │
                    │  │   - LLM classifies conflict type    │   │
                    │  │   - Execute action (merge/delete)   │   │
                    │  │   - Store decision in cache         │   │
                    │  └─────────────────────────────────────┘   │
                    └─────────────────────────────────────────────┘
```

---

## Schema Design

### 1. Add Version Column to story_nodes

```sql
-- Add version tracking to existing table
ALTER TABLE story_nodes ADD COLUMN version INTEGER DEFAULT 1;
```

**Rule**: Increment `version` whenever `title`, `description`, or `status` changes.

### 2. Create vetting_decisions Table

```sql
CREATE TABLE IF NOT EXISTS vetting_decisions (
    -- Primary key: canonical pair ordering (smaller ID first)
    pair_key TEXT PRIMARY KEY,

    -- Version numbers at time of decision (for invalidation)
    story_a_id TEXT NOT NULL,
    story_a_version INTEGER NOT NULL,
    story_b_id TEXT NOT NULL,
    story_b_version INTEGER NOT NULL,

    -- Classification result
    classification TEXT NOT NULL CHECK (classification IN (
        'duplicate', 'scope_overlap', 'competing', 'incompatible', 'false_positive'
    )),

    -- Action taken (for audit trail)
    action_taken TEXT CHECK (action_taken IN (
        'SKIP', 'DELETE_CONCEPT', 'REJECT_CONCEPT', 'BLOCK_CONCEPT',
        'TRUE_MERGE', 'PICK_BETTER', 'HUMAN_REVIEW', 'DEFER_PENDING'
    )),

    -- Metadata
    decided_at TEXT NOT NULL,  -- ISO 8601 timestamp

    -- Foreign keys (soft - stories may be deleted)
    FOREIGN KEY (story_a_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (story_b_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);

-- Index for fast lookups by individual story
CREATE INDEX IF NOT EXISTS idx_vetting_story_a ON vetting_decisions(story_a_id);
CREATE INDEX IF NOT EXISTS idx_vetting_story_b ON vetting_decisions(story_b_id);
```

### 3. Pair Key Format

Canonical ordering ensures consistent lookup regardless of comparison order:

```python
def make_pair_key(id_a: str, id_b: str) -> str:
    """Create canonical pair key with smaller ID first."""
    if id_a < id_b:
        return f"{id_a}|{id_b}"
    else:
        return f"{id_b}|{id_a}"

# Examples:
# make_pair_key("1.8.4", "1.1") → "1.1|1.8.4"
# make_pair_key("1.1", "1.8.4") → "1.1|1.8.4"
```

---

## Implementation Steps

### Step 1: Schema Migration

Run once to add version column and create cache table:

```python
import sqlite3
from datetime import datetime

def migrate_schema(db_path: str):
    """Add version column and vetting_decisions table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if version column exists
    cursor.execute("PRAGMA table_info(story_nodes)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'version' not in columns:
        cursor.execute("ALTER TABLE story_nodes ADD COLUMN version INTEGER DEFAULT 1")
        print("Added 'version' column to story_nodes")

    # Create vetting_decisions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vetting_decisions (
            pair_key TEXT PRIMARY KEY,
            story_a_id TEXT NOT NULL,
            story_a_version INTEGER NOT NULL,
            story_b_id TEXT NOT NULL,
            story_b_version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            action_taken TEXT,
            decided_at TEXT NOT NULL
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vetting_story_a ON vetting_decisions(story_a_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vetting_story_b ON vetting_decisions(story_b_id)')

    conn.commit()
    conn.close()
    print("Schema migration complete")
```

### Step 2: Version Increment on Story Changes

Wrap story updates to auto-increment version:

```python
def update_story(conn, story_id: str, **fields):
    """Update story fields and increment version."""
    set_clauses = ', '.join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [story_id]

    conn.execute(f'''
        UPDATE story_nodes
        SET {set_clauses}, version = COALESCE(version, 0) + 1
        WHERE id = ?
    ''', values)
    conn.commit()
```

### Step 3: Cache Lookup Function

```python
def get_cached_decision(conn, id_a: str, id_b: str) -> dict | None:
    """
    Look up cached decision for a pair.
    Returns None if not cached or if versions don't match (invalidated).
    """
    pair_key = make_pair_key(id_a, id_b)

    # Get cached decision
    cached = conn.execute('''
        SELECT story_a_id, story_a_version, story_b_id, story_b_version,
               classification, action_taken
        FROM vetting_decisions
        WHERE pair_key = ?
    ''', (pair_key,)).fetchone()

    if not cached:
        return None

    # Get current versions
    current_versions = {}
    for story_id in (cached[0], cached[2]):  # story_a_id, story_b_id
        row = conn.execute(
            'SELECT version FROM story_nodes WHERE id = ?', (story_id,)
        ).fetchone()
        if row is None:
            # Story was deleted - invalidate cache entry
            conn.execute('DELETE FROM vetting_decisions WHERE pair_key = ?', (pair_key,))
            conn.commit()
            return None
        current_versions[story_id] = row[0] or 1

    # Check if versions match
    if (current_versions[cached[0]] != cached[1] or
        current_versions[cached[2]] != cached[3]):
        # Versions changed - cache is stale
        return None

    return {
        'pair_key': pair_key,
        'classification': cached[4],
        'action_taken': cached[5],
        'valid': True
    }
```

### Step 4: Cache Write Function

```python
def store_decision(conn, id_a: str, id_b: str, classification: str, action_taken: str):
    """Store classification decision in cache."""
    pair_key = make_pair_key(id_a, id_b)

    # Get current versions
    ver_a = conn.execute('SELECT version FROM story_nodes WHERE id = ?', (id_a,)).fetchone()
    ver_b = conn.execute('SELECT version FROM story_nodes WHERE id = ?', (id_b,)).fetchone()

    # Ensure canonical ordering in storage
    if id_a < id_b:
        story_a_id, story_a_ver = id_a, (ver_a[0] if ver_a else 1)
        story_b_id, story_b_ver = id_b, (ver_b[0] if ver_b else 1)
    else:
        story_a_id, story_a_ver = id_b, (ver_b[0] if ver_b else 1)
        story_b_id, story_b_ver = id_a, (ver_a[0] if ver_a else 1)

    conn.execute('''
        INSERT OR REPLACE INTO vetting_decisions
        (pair_key, story_a_id, story_a_version, story_b_id, story_b_version,
         classification, action_taken, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pair_key, story_a_id, story_a_ver, story_b_id, story_b_ver,
        classification, action_taken, datetime.now().isoformat()
    ))
    conn.commit()
```

### Step 5: Integrate into Phase 1

Modify the candidate detection to filter cached pairs:

```python
def detect_candidates_with_cache(conn, stories: list) -> list:
    """
    Detect candidate conflict pairs, skipping cached false_positives.
    Returns only pairs that need LLM classification.
    """
    candidates = []
    cache_hits = {'false_positive': 0, 'other': 0, 'stale': 0}

    # ... existing heuristic detection code ...

    for pair in potential_candidates:
        id_a, id_b = pair['story_a']['id'], pair['story_b']['id']

        # Check cache
        cached = get_cached_decision(conn, id_a, id_b)

        if cached:
            if cached['classification'] == 'false_positive':
                cache_hits['false_positive'] += 1
                continue  # Skip - already decided as false positive
            else:
                # Non-false-positive cached - might need re-action if interrupted
                cache_hits['other'] += 1
                pair['cached_classification'] = cached['classification']
                pair['cached_action'] = cached['action_taken']
        else:
            cache_hits['stale'] += 1  # Cache miss or invalidated

        candidates.append(pair)

    print(f"Cache stats: {cache_hits['false_positive']} false_positives skipped, "
          f"{cache_hits['other']} other cached, {cache_hits['stale']} need classification")

    return candidates
```

### Step 6: Integrate into Phase 2

After each LLM classification, store the result:

```python
def process_candidate(conn, pair: dict, classification: str, action_taken: str):
    """Process a candidate pair and cache the decision."""
    id_a = pair['story_a']['id']
    id_b = pair['story_b']['id']

    # Execute the action (merge, delete, etc.)
    execute_action(conn, pair, classification, action_taken)

    # Store decision in cache (even for false_positives)
    store_decision(conn, id_a, id_b, classification, action_taken)
```

---

## Expected Behavior

### First Run (Cold Cache)
- All 238 candidates processed by LLM
- All decisions stored in cache
- ~150-180 false_positives cached for future skipping

### Subsequent Runs (Warm Cache)
- Phase 1 generates same ~238 candidates
- Cache lookup filters out ~150-180 false_positives
- Only ~50-90 pairs need LLM review
- **If no stories changed**: Nearly all pairs skipped

### After Story Edit
- Edited story gets `version` incremented
- All cached pairs involving that story become stale
- Those pairs re-enter Phase 2 for fresh classification

### After Story Deletion
- CASCADE delete removes related cache entries
- Or: soft invalidation on next lookup (story not found)

---

## Testing Checklist

1. [ ] Schema migration runs without errors
2. [ ] Version increments on story update
3. [ ] Cache stores decisions correctly
4. [ ] Cache lookup returns valid decisions
5. [ ] Cache invalidates when version changes
6. [ ] Phase 1 skips cached false_positives
7. [ ] Interrupted run can resume (cached decisions preserved)
8. [ ] Deleted stories don't break cache lookups

---

## Current Implementation Status

### Key Files
- `.claude/skills/story-vetting/SKILL.md` - Complete skill documentation with decision matrix
- `.claude/skills/story-vetting/vetting_processor.py` - Phase 2 processor (incomplete)
- `.claude/data/story-tree.db` - SQLite database with story_nodes and story_paths tables
- `.claude/skills/story-tree/references/schema.sql` - Database schema reference

### What Exists
- Phase 1 heuristics: **Complete** (in SKILL.md)
- Phase 2 classification: **Complete** (in SKILL.md)
- Decision matrix: **Complete** (in SKILL.md)

### What Needs Implementation
1. Schema migration (add `version` column, create `vetting_decisions` table)
2. Cache lookup/store functions
3. Integration into Phase 1 candidate filtering
4. Integration into Phase 2 result storage

---

## References

- Story-vetting skill: `.claude/skills/story-vetting/SKILL.md`
- Story-tree schema: `.claude/skills/story-tree/references/schema.sql`
- SQL query patterns: `.claude/skills/story-tree/references/sql-queries.md`
