# Problem Space Detection Schema

> Schema extension for detecting conflicting and duplicate stories through semantic similarity of user story components.

## Overview

This schema extends the existing story-tree database to support:
1. **Component extraction** - Parse stories into role, context, want, benefit
2. **Problem spaces** - Group stories addressing the same underlying problem
3. **Conflict detection** - Flag stories with competing approaches
4. **Resolution tracking** - Record decisions about how conflicts were resolved

## Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Detect, don't auto-merge** | Automatic merging loses nuance; flag for human review |
| **Preserve original text** | Store both original and normalized versions |
| **Lazy embedding** | Compute embeddings on-demand, cache for reuse |
| **Explicit resolution** | Conflicts must be explicitly resolved, not ignored |

---

## Schema Extension

### New Tables

```sql
-- ============================================================================
-- STORY COMPONENTS
-- Parsed user story parts for semantic comparison
-- ============================================================================

CREATE TABLE IF NOT EXISTS story_components (
    story_id TEXT PRIMARY KEY REFERENCES story_nodes(id) ON DELETE CASCADE,

    -- Original extracted text (may be NULL if story doesn't follow format)
    role_original TEXT,           -- "As a [lawyer]"
    context_original TEXT,        -- "who is [working on a file]"
    want_original TEXT,           -- "I want [to see retainer balance]"
    benefit_original TEXT,        -- "So that [I know available funds]"

    -- Normalized versions (after merging with problem space)
    role_normalized TEXT,
    want_normalized TEXT,
    benefit_normalized TEXT,

    -- Link to problem space (NULL until classified)
    problem_space_id TEXT REFERENCES problem_spaces(id),

    -- Extraction metadata
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    extraction_confidence REAL,   -- 0.0-1.0, how well it parsed
    extraction_method TEXT        -- 'regex', 'llm', 'manual'
);

-- ============================================================================
-- EMBEDDINGS CACHE
-- Store computed embeddings to avoid recomputation
-- ============================================================================

CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What this embedding represents
    source_type TEXT NOT NULL,    -- 'story_want', 'story_benefit', 'problem_space'
    source_id TEXT NOT NULL,      -- story_id or problem_space_id
    source_field TEXT NOT NULL,   -- 'want_original', 'benefit_original', etc.

    -- The text that was embedded
    source_text TEXT NOT NULL,

    -- Embedding data (stored as JSON array for SQLite compatibility)
    embedding_model TEXT NOT NULL,     -- 'text-embedding-3-small', 'all-MiniLM-L6-v2'
    embedding_dimensions INTEGER,       -- 384, 1536, etc.
    embedding_vector TEXT NOT NULL,     -- JSON array: [0.123, -0.456, ...]

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(source_type, source_id, source_field, embedding_model)
);

-- ============================================================================
-- PROBLEM SPACES
-- Normalized groupings of stories addressing the same problem
-- ============================================================================

CREATE TABLE IF NOT EXISTS problem_spaces (
    id TEXT PRIMARY KEY,          -- Auto-generated: 'PS-001', 'PS-002', etc.

    -- Normalized description of the problem
    name TEXT NOT NULL,           -- Short name: "Trust Account Visibility"
    want_normalized TEXT,         -- Canonical "want" for this space
    benefit_normalized TEXT,      -- Canonical "benefit" for this space

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN (
            'open',               -- Newly created, needs review
            'reviewed',           -- Human has reviewed, no conflict
            'conflict',           -- Multiple competing approaches detected
            'resolved',           -- Conflict resolved, decision made
            'archived'            -- No longer relevant
        )),

    -- Resolution details (populated when status = 'resolved')
    resolution_type TEXT          -- 'merged', 'superseded', 'split', 'pending'
        CHECK (resolution_type IN (
            'merged',             -- Stories combined into one approach
            'superseded',         -- One story chosen, others rejected
            'split',              -- Problem was actually multiple problems
            'coexist',            -- Stories can coexist (different scopes)
            'pending'            -- Decision postponed
        )),
    resolution_notes TEXT,        -- Why this resolution was chosen
    resolution_story_id TEXT,     -- The "winner" story if superseded
    resolved_at TEXT,
    resolved_by TEXT,             -- 'user', 'orchestrator', etc.

    -- ADR link (if architectural decision was made)
    adr_reference TEXT,           -- Path to ADR file if one was created

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- SIMILARITY SCORES
-- Pre-computed similarity between stories for quick lookup
-- ============================================================================

CREATE TABLE IF NOT EXISTS similarity_scores (
    story_id_a TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    story_id_b TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,

    -- Component-level similarities (0.0 to 1.0)
    role_similarity REAL,
    want_similarity REAL,
    benefit_similarity REAL,

    -- Overall similarity (weighted combination)
    overall_similarity REAL NOT NULL,

    -- Classification
    relationship_type TEXT
        CHECK (relationship_type IN (
            'duplicate',          -- Same story, different words
            'variant',            -- Same problem, slightly different scope
            'competing',          -- Same problem, different approach
            'related',            -- Overlapping concerns
            'independent'         -- No meaningful relationship
        )),

    -- Metadata
    computed_at TEXT NOT NULL DEFAULT (datetime('now')),
    embedding_model TEXT,         -- Which model was used

    PRIMARY KEY (story_id_a, story_id_b),
    CHECK (story_id_a < story_id_b)  -- Ensure consistent ordering
);

-- ============================================================================
-- CONFLICT FLAGS
-- Explicit flags for stories needing human review
-- ============================================================================

CREATE TABLE IF NOT EXISTS conflict_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- The stories involved
    story_id_a TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    story_id_b TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    problem_space_id TEXT REFERENCES problem_spaces(id),

    -- What kind of conflict
    conflict_type TEXT NOT NULL
        CHECK (conflict_type IN (
            'duplicate',          -- Essentially the same story
            'scope_overlap',      -- One subsumes the other
            'architectural',      -- Incompatible technical approaches
            'sequencing',         -- Circular or conflicting dependencies
            'resource',           -- Compete for same limited resource
            'semantic'            -- AI detected similarity, needs review
        )),

    -- Severity
    severity TEXT NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    -- Status
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'reviewing', 'resolved', 'dismissed')),

    -- Resolution
    resolution TEXT,              -- How it was resolved
    resolved_at TEXT,

    -- Detection metadata
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    detected_by TEXT,             -- 'orchestrator', 'user', 'similarity_scan'
    detection_confidence REAL,    -- 0.0-1.0

    UNIQUE(story_id_a, story_id_b, conflict_type)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_components_problem_space
    ON story_components(problem_space_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_source
    ON embeddings(source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_similarity_overall
    ON similarity_scores(overall_similarity DESC);

CREATE INDEX IF NOT EXISTS idx_similarity_story_a
    ON similarity_scores(story_id_a);

CREATE INDEX IF NOT EXISTS idx_similarity_story_b
    ON similarity_scores(story_id_b);

CREATE INDEX IF NOT EXISTS idx_conflicts_status
    ON conflict_flags(status);

CREATE INDEX IF NOT EXISTS idx_conflicts_story_a
    ON conflict_flags(story_id_a);

CREATE INDEX IF NOT EXISTS idx_problem_spaces_status
    ON problem_spaces(status);
```

---

## Data Flow

### 1. Story Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEW STORY INSERTED                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Extract Components                                              │
│  ───────────────────────────────────────────────────────────────────────│
│  Parse description into: role, context, want, benefit                    │
│  Store in story_components with extraction_confidence                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Compute Embeddings                                              │
│  ───────────────────────────────────────────────────────────────────────│
│  Embed want_original and benefit_original                                │
│  Store in embeddings table                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Find Similar Stories                                            │
│  ───────────────────────────────────────────────────────────────────────│
│  Compare embeddings against all existing stories                         │
│  Compute similarity_scores for pairs above threshold (0.7)               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────┴───────────────┐
                    │                               │
            [similarity > 0.85]            [similarity < 0.85]
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────────┐
│  STEP 4a: Flag Conflict       │   │  STEP 4b: Create Problem Space    │
│  ─────────────────────────────│   │  ─────────────────────────────────│
│  Create conflict_flag         │   │  Create new problem_space         │
│  Link both to problem_space   │   │  Link story to it                 │
│  Set status = 'open'          │   │  No conflict flag needed          │
└───────────────────────────────┘   └───────────────────────────────────┘
```

### 2. Conflict Resolution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEWS CONFLICT FLAG                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            [DISMISS]       [MERGE STORIES]   [SUPERSEDE]
                    │               │               │
                    ▼               ▼               ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────────┐
│ Update conflict_flag│ │ Create normalized   │ │ Mark loser as           │
│ status='dismissed'  │ │ want/benefit in     │ │ status='rejected' or    │
│                     │ │ problem_space       │ │ 'superseded'            │
│                     │ │                     │ │                         │
│                     │ │ Update both stories │ │ Update problem_space    │
│                     │ │ to use normalized   │ │ resolution_story_id     │
└─────────────────────┘ └─────────────────────┘ └─────────────────────────┘
```

---

## Example Queries

### Find All Unresolved Conflicts

```sql
SELECT
    cf.id,
    cf.conflict_type,
    cf.severity,
    s1.id as story_a_id,
    s1.title as story_a_title,
    s2.id as story_b_id,
    s2.title as story_b_title,
    ss.overall_similarity
FROM conflict_flags cf
JOIN story_nodes s1 ON cf.story_id_a = s1.id
JOIN story_nodes s2 ON cf.story_id_b = s2.id
LEFT JOIN similarity_scores ss
    ON (ss.story_id_a = cf.story_id_a AND ss.story_id_b = cf.story_id_b)
WHERE cf.status = 'open'
ORDER BY cf.severity DESC, ss.overall_similarity DESC;
```

### Find Stories in Same Problem Space

```sql
SELECT
    ps.id as problem_space,
    ps.name,
    ps.status as space_status,
    s.id as story_id,
    s.title,
    s.status as story_status,
    sc.want_original,
    sc.benefit_original
FROM problem_spaces ps
JOIN story_components sc ON sc.problem_space_id = ps.id
JOIN story_nodes s ON s.id = sc.story_id
WHERE ps.status IN ('open', 'conflict')
ORDER BY ps.id, s.id;
```

### Find Most Similar Story to New Input

```sql
-- Given a new story's want embedding, find closest matches
-- (In practice, this would be done in Python with numpy)

SELECT
    s.id,
    s.title,
    sc.want_original,
    e.source_text
FROM embeddings e
JOIN story_components sc ON e.source_id = sc.story_id
JOIN story_nodes s ON s.id = sc.story_id
WHERE e.source_type = 'story_want'
    AND e.source_field = 'want_original'
    AND s.status NOT IN ('rejected', 'archived', 'deprecated')
ORDER BY s.created_at DESC
LIMIT 20;
-- Then compute cosine similarity in Python
```

### Problem Space Statistics

```sql
SELECT
    ps.status,
    COUNT(*) as space_count,
    SUM(story_count) as total_stories,
    AVG(story_count) as avg_stories_per_space
FROM problem_spaces ps
LEFT JOIN (
    SELECT problem_space_id, COUNT(*) as story_count
    FROM story_components
    GROUP BY problem_space_id
) sc ON ps.id = sc.problem_space_id
GROUP BY ps.status;
```

---

## Component Extraction

### Regex-Based Extraction (Fast, Less Accurate)

```python
import re

def extract_components_regex(description: str) -> dict:
    """Extract user story components using regex patterns."""

    patterns = {
        'role': r"[Aa]s (?:a|an) ([^,\n]+)",
        'context': r"who (?:is|are|wants to be) ([^,\n]+)",
        'want': r"[Ii] want (?:to )?([^,\n]+?)(?:\s+[Ss]o that|\s*$)",
        'benefit': r"[Ss]o that ([^,\n]+)"
    }

    result = {
        'role_original': None,
        'context_original': None,
        'want_original': None,
        'benefit_original': None,
        'extraction_confidence': 0.0,
        'extraction_method': 'regex'
    }

    matches = 0
    for key, pattern in patterns.items():
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            result[f'{key}_original'] = match.group(1).strip()
            matches += 1

    result['extraction_confidence'] = matches / 4.0
    return result
```

### LLM-Based Extraction (Slower, More Accurate)

```python
def extract_components_llm(description: str) -> dict:
    """Extract user story components using Claude."""

    prompt = f"""Extract user story components from this text.
Return JSON with these fields (use null if not found):
- role: The user role (after "As a")
- context: Additional context about the situation (after "who is" or similar)
- want: What the user wants (after "I want")
- benefit: The benefit/outcome (after "So that")

Text: {description}

JSON:"""

    # Call Claude API here
    response = call_claude(prompt)

    result = json.loads(response)
    result['extraction_method'] = 'llm'
    result['extraction_confidence'] = 0.95  # LLM is usually high confidence

    return result
```

---

## Similarity Computation

### Cosine Similarity with Embeddings

```python
import numpy as np
from typing import List, Tuple

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_story_similarity(
    story_a_components: dict,
    story_b_components: dict,
    embeddings_a: dict,
    embeddings_b: dict
) -> dict:
    """Compute similarity scores between two stories."""

    # Component weights for overall score
    weights = {
        'role': 0.1,      # Role similarity matters less
        'want': 0.5,      # What they want is most important
        'benefit': 0.4    # Why they want it is also key
    }

    similarities = {}
    overall = 0.0

    for component, weight in weights.items():
        key = f'{component}_original'
        if key in embeddings_a and key in embeddings_b:
            sim = cosine_similarity(
                embeddings_a[key],
                embeddings_b[key]
            )
            similarities[f'{component}_similarity'] = sim
            overall += sim * weight
        else:
            similarities[f'{component}_similarity'] = None

    similarities['overall_similarity'] = overall

    # Classify relationship
    if overall > 0.92:
        similarities['relationship_type'] = 'duplicate'
    elif overall > 0.85:
        similarities['relationship_type'] = 'variant'
    elif overall > 0.75:
        similarities['relationship_type'] = 'competing'
    elif overall > 0.60:
        similarities['relationship_type'] = 'related'
    else:
        similarities['relationship_type'] = 'independent'

    return similarities
```

---

## Integration with Orchestrator

### Modified Story Creation Flow

```python
def on_story_created(story_id: str, description: str):
    """Hook called after a new story is inserted."""

    # 1. Extract components
    components = extract_components_regex(description)
    if components['extraction_confidence'] < 0.5:
        components = extract_components_llm(description)

    save_components(story_id, components)

    # 2. Compute embeddings
    embeddings = {}
    for field in ['want_original', 'benefit_original']:
        if components.get(field):
            embeddings[field] = compute_embedding(components[field])
            save_embedding(story_id, field, embeddings[field])

    # 3. Find similar stories
    similar = find_similar_stories(story_id, embeddings, threshold=0.7)

    # 4. Handle matches
    for match in similar:
        if match['overall_similarity'] > 0.85:
            # High similarity - create conflict flag
            create_conflict_flag(
                story_id_a=min(story_id, match['story_id']),
                story_id_b=max(story_id, match['story_id']),
                conflict_type='semantic',
                severity='medium' if match['overall_similarity'] < 0.92 else 'high',
                detection_confidence=match['overall_similarity']
            )

        # Save similarity score regardless
        save_similarity_score(story_id, match['story_id'], match)

    # 5. Assign to problem space
    problem_space = find_or_create_problem_space(story_id, similar)
    update_story_problem_space(story_id, problem_space)
```

### Orchestrator Conflict Check Job

Add a new step to the orchestrator workflow:

```yaml
# In story-tree-orchestrator.yml, after write-stories step:

- name: Check for conflicts
  run: |
    conflict_count=$(python -c "
    import sqlite3
    conn = sqlite3.connect('.claude/data/story-tree.db')
    count = conn.execute('''
        SELECT COUNT(*) FROM conflict_flags
        WHERE status = 'open' AND severity IN ('high', 'critical')
    ''').fetchone()[0]
    print(count)
    ")

    if [ "$conflict_count" -gt 0 ]; then
      echo "::warning::$conflict_count high-severity conflicts need review"
      echo "| Conflicts | $conflict_count |" >> "$PROGRESS_FILE"
    fi
```

---

## Migration Script

```python
#!/usr/bin/env python3
"""
Migrate story-tree.db to add problem space detection tables.
Run: python .claude/scripts/migrate_problem_spaces.py
"""

import sqlite3
from pathlib import Path

DB_PATH = '.claude/data/story-tree.db'
SCHEMA_VERSION = '4.0.0'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current version
    cursor.execute("SELECT value FROM metadata WHERE key = 'version'")
    row = cursor.fetchone()
    current_version = row[0] if row else '3.0.0'

    if current_version >= SCHEMA_VERSION:
        print(f"Already at version {current_version}, skipping migration")
        return

    print(f"Migrating from {current_version} to {SCHEMA_VERSION}")

    # Create new tables (idempotent with IF NOT EXISTS)
    cursor.executescript("""
        -- [Insert all CREATE TABLE statements from above]
    """)

    # Backfill story_components for existing stories
    cursor.execute("SELECT id, description FROM story_nodes")
    stories = cursor.fetchall()

    for story_id, description in stories:
        # Extract components (simplified for migration)
        cursor.execute("""
            INSERT OR IGNORE INTO story_components (story_id, extraction_method)
            VALUES (?, 'pending')
        """, (story_id,))

    # Update version
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('version', ?)
    """, (SCHEMA_VERSION,))

    conn.commit()
    conn.close()

    print(f"Migration complete. {len(stories)} stories queued for component extraction.")

if __name__ == '__main__':
    migrate()
```

---

## Thresholds and Tuning

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SIMILARITY_THRESHOLD_STORE` | 0.60 | Minimum similarity to store in similarity_scores |
| `SIMILARITY_THRESHOLD_FLAG` | 0.85 | Minimum similarity to create conflict_flag |
| `SIMILARITY_THRESHOLD_DUPLICATE` | 0.92 | Similarity above this = likely duplicate |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI model for embeddings |
| `EMBEDDING_DIMENSIONS` | 1536 | Vector size |
| `MAX_COMPARISONS_PER_STORY` | 100 | Limit comparisons for performance |

---

## References

- Current schema: `.claude/skills/story-tree/references/schema.sql`
- Story writing skill: `.claude/skills/story-writing/SKILL.md`
- Orchestrator workflow: `.github/workflows/story-tree-orchestrator.yml`
- Orchestrator docs: `ai_docs/Orchestrator/2025-12-16-Dev-Workflow.md`
