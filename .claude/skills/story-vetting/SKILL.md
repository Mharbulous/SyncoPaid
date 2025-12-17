---
name: story-vetting
description: Use when orchestrator generates new stories or user says "vet stories", "check conflicts", "find duplicates", "scan for overlaps" - scans story-tree database to detect duplicate, overlapping, or competing stories. Returns conflict pairs with types and confidence scores for human review.
---

# Story Vetting - Automated Concept Conflict Resolution

Detect and resolve conflicting concepts in the story-tree database. This skill **vets concepts** before presenting them to humans - most conflicts are resolved automatically.

**Database:** `.claude/data/story-tree.db`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

**Platform Note:** All Python commands use `python` (not `python3`) for cross-platform compatibility.

## Architecture Overview

```
Phase 1: Candidate Detection (Python script)
├── Run keyword/similarity heuristics
├── Output CANDIDATE pairs (potential conflicts)
└── No classification — just "these might conflict"

Phase 2: Classification & Resolution (Main Agent)
├── For each candidate pair:
│   ├── Read both story descriptions
│   ├── Classify: duplicate / scope_overlap / competing / incompatible / false_positive
│   ├── Look up action (deterministic based on classification + status)
│   └── Execute action (LLM for merges, Python for deletes/status updates)
└── Present only HUMAN REVIEW cases interactively
```

## Decision Matrix

The skill vets **concepts only** — deciding what ideas to present to the human.

### Conflict Types

| Type | Description |
|------|-------------|
| `duplicate` | Essentially the same story |
| `scope_overlap` | One subsumes or partially covers another |
| `competing` | Same problem, different/incompatible approaches |
| `incompatible` | Mutually exclusive approaches that cannot be merged |
| `false_positive` | Flagged by heuristics but not actually conflicting |

### Automated Actions

| Conflict Type | Concept vs... | Action |
|---------------|---------------|--------|
| **DUPLICATE** | `wishlist`, `refine` | TRUE MERGE → keep status |
| **DUPLICATE** | `concept` | TRUE MERGE → concept |
| **DUPLICATE** | everything else | DELETE concept |
| **SCOPE_OVERLAP** | `concept` | TRUE MERGE → concept |
| **SCOPE_OVERLAP** | any other | HUMAN REVIEW |
| **COMPETING** | `concept`, `wishlist`, `refine` | TRUE MERGE |
| **COMPETING** | `rejected`, `infeasible`, `broken`, `pending`, `blocked` | BLOCK concept with note |
| **COMPETING** | everything else | AUTO-REJECT with note |
| **INCOMPATIBLE** | `concept` | Claude picks better, DELETE other |
| **FALSE_POSITIVE** | — | SKIP (no action) |
| **Non-concept vs non-concept** | — | IGNORE |

### Status Reference

**Mergeable with concepts:** `concept`, `wishlist`, `refine`

**Block against:** `rejected`, `infeasible`, `broken`, `pending`, `blocked`

**Auto-delete/reject against:** `approved`, `planned`, `implemented`, `queued`, `paused`, `active`, `reviewing`, `ready`, `polish`, `released`, `legacy`, `deprecated`, `archived`

---

## CI Mode

When running in CI (non-interactive environment), HUMAN_REVIEW cases cannot prompt for input. Instead:

- **HUMAN_REVIEW → DEFER_PENDING**: Set concept status to `pending` with note explaining the conflict
- All other automated actions work the same

**Detection**: CI mode is active when running in GitHub Actions or when explicitly specified.

---

## Decision Cache

The vetting system uses a persistent cache to avoid re-classifying the same story pairs on each run. This is especially important when running vetting daily, as most pairs will be false positives that don't need repeated LLM analysis.

### How It Works

1. **Version Tracking**: Each `story_nodes` record has a `version` column (INTEGER, default 1)
2. **Cache Storage**: Classification decisions are stored in `vetting_decisions` table with:
   - Canonical pair key (smaller ID first, e.g., `1.1|1.8.4`)
   - Version numbers at time of decision
   - Classification and action taken
3. **Invalidation**: When a story's `title`, `description`, or `status` changes, increment its `version`. All cached pairs involving that story become stale.

### Cache Behavior

- **First run (cold cache)**: All 238 candidates processed by LLM, decisions stored
- **Subsequent runs (warm cache)**: ~150-180 false_positives skipped, only stale/new pairs classified
- **After story edit**: Pairs involving edited story re-enter Phase 2

### CLI Commands

```bash
# Run schema migration (safe to run multiple times)
python .claude/skills/story-vetting/vetting_cache.py migrate

# View cache statistics
python .claude/skills/story-vetting/vetting_cache.py stats

# Clear all cached decisions
python .claude/skills/story-vetting/vetting_cache.py clear
```

---

## Phase 1: Candidate Detection

Run this Python script to find candidate conflict pairs:

```python
python << 'PYEOF'
import sqlite3
import json
import re

def tokenize(text):
    '''Extract lowercase word tokens, removing stopwords.'''
    if not text:
        return set()
    words = re.findall(r'[a-z]+', text.lower())
    stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                 'because', 'until', 'while', 'that', 'this', 'these', 'those',
                 'user', 'want', 'need', 'able', 'feature', 'system', 'data'}
    return set(w for w in words if w not in stopwords and len(w) > 2)

def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def overlap_coefficient(set1, set2):
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / min(len(set1), len(set2))

def find_specific_keywords(text):
    '''Extract specific implementation keywords from description.'''
    if not text:
        return set()
    patterns = {
        'sqlite': 'sqlite',
        r'zip.*compress|compress.*zip': 'archive_compress',
        'monthly': 'monthly_schedule',
        r'archiv(?:e|ing)': 'archiving',
        r'retention|cleanup': 'retention_policy',
        r'block.*(?:list|app)|(?:list|app).*block': 'app_blocking',
        r'privacy.*block|block.*privacy': 'privacy_blocking',
        r'skip.*app|app.*skip': 'app_filtering',
        'crud': 'crud',
        'tkinter': 'tkinter_ui',
        r'idle.*resump|resump.*idle': 'idle_resumption',
        r'transition.*detect|detect.*transition': 'transition_detection',
        'ui automation': 'ui_automation',
        r'learn.*correction|correction.*learn|pattern.*learn': 'ai_learning',
        r'matter.*table|table.*matter': 'matter_table',
        r'client.*table|table.*client': 'client_table',
        r'process.*name|exe.*name': 'process_matching',
    }
    found = set()
    text_lower = text.lower()
    for p, label in patterns.items():
        if re.search(p, text_lower):
            found.add(label)
    return found

def detect_candidates(stories):
    '''Detect candidate conflict pairs for LLM review.'''
    candidates = []
    story_data = {}

    for s in stories:
        story_id = s['id']
        title_tokens = tokenize(s['title'])
        desc_tokens = tokenize(s['description'])
        spec_keywords = find_specific_keywords(s['description'])

        story_data[story_id] = {
            'story': s,
            'title_tokens': title_tokens,
            'desc_tokens': desc_tokens,
            'spec_keywords': spec_keywords
        }

    story_ids = list(story_data.keys())
    for i in range(len(story_ids)):
        for j in range(i + 1, len(story_ids)):
            id_a, id_b = story_ids[i], story_ids[j]
            data_a, data_b = story_data[id_a], story_data[id_b]
            story_a, story_b = data_a['story'], data_b['story']

            # Skip if neither is a concept (non-concept vs non-concept)
            if story_a['status'] != 'concept' and story_b['status'] != 'concept':
                continue

            # Skip parent-child relationships
            if id_a.startswith(id_b + '.') or id_b.startswith(id_a + '.'):
                continue

            # Calculate similarity signals
            spec_shared = data_a['spec_keywords'] & data_b['spec_keywords']
            title_sim = jaccard_similarity(data_a['title_tokens'], data_b['title_tokens'])
            title_overlap = overlap_coefficient(data_a['title_tokens'], data_b['title_tokens'])
            desc_sim = jaccard_similarity(data_a['desc_tokens'], data_b['desc_tokens'])

            # Flag as candidate if any signal is strong enough
            is_candidate = (
                len(spec_shared) >= 1 or
                title_sim > 0.15 or
                title_overlap > 0.4 or
                desc_sim > 0.10
            )

            if is_candidate:
                candidates.append({
                    'story_a': {
                        'id': id_a,
                        'title': story_a['title'],
                        'status': story_a['status'],
                        'description': story_a['description']
                    },
                    'story_b': {
                        'id': id_b,
                        'title': story_b['title'],
                        'status': story_b['status'],
                        'description': story_b['description']
                    },
                    'signals': {
                        'shared_keywords': list(spec_shared),
                        'title_similarity': round(title_sim, 2),
                        'title_overlap': round(title_overlap, 2),
                        'desc_similarity': round(desc_sim, 2)
                    }
                })

    return candidates

# Load stories and run detection
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.status
    FROM story_nodes s
    WHERE s.status NOT IN ('archived', 'deprecated')
    ORDER BY s.id
''').fetchall()]
conn.close()

candidates = detect_candidates(stories)
print(json.dumps({
    'total_stories': len(stories),
    'candidates_found': len(candidates),
    'candidates': candidates
}, indent=2))
PYEOF
```

---

## Phase 2: Classification & Resolution

For each candidate pair from Phase 1, the main agent must:

### Step 1: Classify the Conflict

Read both story descriptions and determine the conflict type:

- **duplicate**: Stories describe essentially the same feature/requirement
- **scope_overlap**: One story's scope partially overlaps with another (but they're distinct)
- **competing**: Same problem, but different/incompatible solution approaches
- **incompatible**: Two concepts with mutually exclusive approaches (cannot merge)
- **false_positive**: Heuristics flagged it, but stories are actually unrelated

### Step 2: Determine Action

Use this lookup based on classification and statuses:

```python
MERGEABLE_STATUSES = {'concept', 'wishlist', 'refine'}
BLOCK_STATUSES = {'rejected', 'infeasible', 'broken', 'pending', 'blocked'}

def get_action(conflict_type, status_a, status_b, ci_mode=False):
    # Ensure concept is always story_a for consistent logic
    if status_b == 'concept' and status_a != 'concept':
        status_a, status_b = status_b, status_a

    if conflict_type == 'false_positive':
        return 'SKIP'

    if conflict_type == 'duplicate':
        if status_b in MERGEABLE_STATUSES:
            return 'TRUE_MERGE'
        else:
            return 'DELETE_CONCEPT'

    if conflict_type == 'scope_overlap':
        if status_a == 'concept' and status_b == 'concept':
            return 'TRUE_MERGE'
        else:
            # In CI mode, defer to pending instead of blocking for human input
            return 'DEFER_PENDING' if ci_mode else 'HUMAN_REVIEW'

    if conflict_type == 'competing':
        if status_b in MERGEABLE_STATUSES:
            return 'TRUE_MERGE'
        elif status_b in BLOCK_STATUSES:
            return 'BLOCK_CONCEPT'
        else:
            return 'REJECT_CONCEPT'

    if conflict_type == 'incompatible':
        # Claude picks the better concept, deletes the other
        return 'PICK_BETTER'

    return 'SKIP'
```

### Step 3: Execute Action

#### DELETE_CONCEPT
Remove the concept from database without trace:

```python
python << PYEOF
import sqlite3
concept_id = "$CONCEPT_ID"
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (concept_id,))
conn.execute('DELETE FROM story_nodes WHERE id = ?', (concept_id,))
conn.commit()
print(f"Deleted concept {concept_id}")
conn.close()
PYEOF
```

#### REJECT_CONCEPT
Set status to rejected with note:

```python
python << PYEOF
import sqlite3
concept_id = "$CONCEPT_ID"
conflicting_id = "$CONFLICTING_ID"
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'rejected',
        notes = COALESCE(notes || char(10), '') || 'Conflicts with story node ' || ?
    WHERE id = ?
''', (conflicting_id, concept_id))
conn.commit()
print(f"Rejected concept {concept_id} (conflicts with {conflicting_id})")
conn.close()
PYEOF
```

#### BLOCK_CONCEPT
Set status to blocked with note:

```python
python << PYEOF
import sqlite3
concept_id = "$CONCEPT_ID"
conflicting_id = "$CONFLICTING_ID"
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'blocked',
        notes = COALESCE(notes || char(10), '') || 'Blocked due to conflict with story node ' || ?
    WHERE id = ?
''', (conflicting_id, concept_id))
conn.commit()
print(f"Blocked concept {concept_id} (conflicts with {conflicting_id})")
conn.close()
PYEOF
```

#### DEFER_PENDING (CI mode only)
Set concept status to `pending` for later human review:

```python
python << PYEOF
import sqlite3
concept_id = "$CONCEPT_ID"
conflicting_id = "$CONFLICTING_ID"
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute('''
    UPDATE story_nodes
    SET status = 'pending',
        notes = COALESCE(notes || char(10), '') || 'Scope overlap with ' || ? || ' - needs human review'
    WHERE id = ?
''', (conflicting_id, concept_id))
conn.commit()
print(f"Deferred concept {concept_id} to pending (scope overlap with {conflicting_id})")
conn.close()
PYEOF
```

#### TRUE_MERGE
Claude combines best ideas from both stories into a single node:

1. Read both descriptions carefully
2. Create merged title (concise, captures both scopes)
3. Create merged description combining:
   - Best "As a user, I want..." statement
   - Combined acceptance criteria (deduplicated)
   - Any unique details from either story
4. Keep the story with lower/earlier ID (more established in hierarchy)
5. Update that story with merged content
6. Delete the other story

```python
python << PYEOF
import sqlite3
keep_id = "$KEEP_ID"
delete_id = "$DELETE_ID"
merged_title = '''$MERGED_TITLE'''
merged_description = '''$MERGED_DESCRIPTION'''

conn = sqlite3.connect('.claude/data/story-tree.db')
# Update the kept story
conn.execute('''
    UPDATE story_nodes
    SET title = ?, description = ?,
        notes = COALESCE(notes || char(10), '') || 'Merged from story node ' || ?
    WHERE id = ?
''', (merged_title, merged_description, delete_id, keep_id))
# Delete the other story
conn.execute('DELETE FROM story_paths WHERE descendant_id = ?', (delete_id,))
conn.execute('DELETE FROM story_nodes WHERE id = ?', (delete_id,))
conn.commit()
print(f"Merged {delete_id} into {keep_id}")
conn.close()
PYEOF
```

#### PICK_BETTER
For incompatible concepts, Claude evaluates which is better based on:
- Clarity of requirements
- Feasibility
- Alignment with project goals
- Technical soundness

Then DELETE the worse concept and keep the better one unchanged.

#### HUMAN_REVIEW
Present stories side-by-side for human decision:

```
SCOPE OVERLAP - Human Review Required
=====================================

┌─────────────────────────────────────┬─────────────────────────────────────┐
│ Story A: $ID_A ($STATUS_A)          │ Story B: $ID_B ($STATUS_B)          │
├─────────────────────────────────────┼─────────────────────────────────────┤
│ $TITLE_A                            │ $TITLE_B                            │
├─────────────────────────────────────┼─────────────────────────────────────┤
│ $DESCRIPTION_A                      │ $DESCRIPTION_B                      │
└─────────────────────────────────────┴─────────────────────────────────────┘

Signals: shared_keywords=$KEYWORDS, title_sim=$SIM

Options:
  [A] Reject Story A (keep B)
  [B] Reject Story B (keep A)
  [M] True Merge (combine into one)
  [S] Skip (keep both, no conflict)

Your choice:
```

---

## Workflow Summary

1. **Run Phase 1** - Execute candidate detection Python script
2. **Parse results** - Load candidate pairs from JSON output
3. **For each candidate:**
   - Read both story descriptions
   - Classify conflict type (duplicate/scope_overlap/competing/incompatible/false_positive)
   - Look up action from decision matrix (pass `ci_mode=True` in CI environment)
   - Execute action (auto for most, DEFER_PENDING for scope overlaps in CI)
4. **Report summary** - Show counts of actions taken

### Expected Output (Interactive)

```
STORY VETTING COMPLETE
======================

Candidates scanned: 45
Actions taken:
  - Deleted: 8 duplicate concepts
  - Merged: 12 concept pairs
  - Rejected: 3 competing concepts
  - Blocked: 2 concepts
  - Skipped: 15 false positives
  - Human review: 5 scope overlaps

Human review required for 5 conflicts (see above).
```

### Expected Output (CI Mode)

```
STORY VETTING COMPLETE (CI MODE)
================================

Candidates scanned: 45
Actions taken:
  - Deleted: 8 duplicate concepts
  - Merged: 12 concept pairs
  - Rejected: 3 competing concepts
  - Blocked: 2 concepts
  - Skipped: 15 false positives
  - Deferred to pending: 5 scope overlaps

5 concepts set to 'pending' status for later human review.
```

---

## References

- **Database:** `.claude/data/story-tree.db`
- **Schema:** `.claude/skills/story-tree/references/schema.sql`
- **SQL Queries:** `.claude/skills/story-tree/references/sql-queries.md`
