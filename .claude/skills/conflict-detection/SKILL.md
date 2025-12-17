---
name: conflict-detection
description: Use when orchestrator generates new stories or user says "check conflicts", "find duplicates", "scan for overlaps" - scans story-tree database to detect duplicate, overlapping, or competing stories. Returns conflict pairs with types and confidence scores for human review.
---

# Conflict Detection - Lightweight Story Conflict Scanner

Detect duplicate, overlapping, and competing stories in the story-tree database.

**Database:** `.claude/data/story-tree.db`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Conflict Types

| Type | Description | Detection Method |
|------|-------------|------------------|
| `duplicate` | Essentially the same story | High title + description similarity (>0.7) |
| `scope_overlap` | One subsumes or partially covers another | Sibling stories with shared keywords (>0.5) |
| `competing` | Same problem, incompatible approaches | Similar "I want" but different solutions |

## Workflow

### Step 1: Load Stories for Comparison

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row

# Get active stories (exclude archived, rejected, deprecated)
stories = [dict(row) for row in conn.execute('''
    SELECT
        s.id, s.title, s.description, s.status,
        (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
    FROM story_nodes s
    WHERE s.status NOT IN ('rejected', 'archived', 'deprecated', 'infeasible')
    ORDER BY s.id
''').fetchall()]

print(json.dumps({'count': len(stories), 'stories': stories}, indent=2))
conn.close()
"
```

### Step 2: Run Conflict Detection Algorithm

The algorithm uses lightweight text similarity (no external dependencies):

```python
python -c "
import sqlite3
import json
import re
from collections import Counter

def tokenize(text):
    '''Extract lowercase word tokens, removing punctuation.'''
    if not text:
        return set()
    words = re.findall(r'[a-z]+', text.lower())
    # Remove common stopwords AND domain-specific boilerplate
    stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                 'from', 'as', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'between', 'under', 'again', 'further',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                 'because', 'until', 'while', 'that', 'this', 'these', 'those',
                 'i', 'want', 'so',
                 # Domain-specific boilerplate (reduces false positives)
                 'lawyer', 'criteria', 'acceptance', 'context', 'related',
                 'vision', 'alignment', 'core', 'capability', 'guiding',
                 'principle', 'target', 'user', 'litigation', 'civil',
                 'syncopaid', 'tracking', 'capture', 'time', 'activity',
                 'activities', 'billable', 'billing'}
    return set(w for w in words if w not in stopwords and len(w) > 2)

def jaccard_similarity(set1, set2):
    '''Compute Jaccard similarity between two sets.'''
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def extract_user_story_parts(description):
    '''Extract As a/I want/So that components from user story.'''
    parts = {'role': '', 'want': '', 'benefit': ''}
    if not description:
        return parts

    # Extract role (As a...)
    role_match = re.search(r'[Aa]s (?:a|an) ([^\n]+?)(?:\n|I want|$)', description)
    if role_match:
        parts['role'] = role_match.group(1).strip()

    # Extract want (I want...)
    want_match = re.search(r'[Ii] want (?:to )?([^\n]+?)(?:\n|[Ss]o that|$)', description)
    if want_match:
        parts['want'] = want_match.group(1).strip()

    # Extract benefit (So that...)
    benefit_match = re.search(r'[Ss]o that ([^\n]+?)(?:\n|$)', description)
    if benefit_match:
        parts['benefit'] = benefit_match.group(1).strip()

    return parts

def detect_conflicts(stories):
    '''Detect conflicts between story pairs.'''
    conflicts = []
    n = len(stories)

    # Pre-compute tokens and story parts
    story_data = {}
    for s in stories:
        story_id = s['id']
        title_tokens = tokenize(s['title'])
        desc_tokens = tokenize(s['description'])
        parts = extract_user_story_parts(s['description'])
        want_tokens = tokenize(parts['want'])
        benefit_tokens = tokenize(parts['benefit'])

        story_data[story_id] = {
            'story': s,
            'title_tokens': title_tokens,
            'desc_tokens': desc_tokens,
            'all_tokens': title_tokens | desc_tokens,
            'want_tokens': want_tokens,
            'benefit_tokens': benefit_tokens,
            'parts': parts
        }

    # Compare all pairs
    story_ids = list(story_data.keys())
    for i in range(len(story_ids)):
        for j in range(i + 1, len(story_ids)):
            id_a, id_b = story_ids[i], story_ids[j]
            data_a, data_b = story_data[id_a], story_data[id_b]

            # Skip if one is ancestor of other (natural hierarchy)
            if id_a.startswith(id_b + '.') or id_b.startswith(id_a + '.'):
                continue

            # Calculate similarities
            title_sim = jaccard_similarity(data_a['title_tokens'], data_b['title_tokens'])
            desc_sim = jaccard_similarity(data_a['desc_tokens'], data_b['desc_tokens'])
            want_sim = jaccard_similarity(data_a['want_tokens'], data_b['want_tokens'])
            benefit_sim = jaccard_similarity(data_a['benefit_tokens'], data_b['benefit_tokens'])

            # Overall similarity (weighted)
            overall = (title_sim * 0.3) + (desc_sim * 0.3) + (want_sim * 0.25) + (benefit_sim * 0.15)

            conflict = None

            # Check for DUPLICATE: high overall similarity
            if overall > 0.5 or (title_sim > 0.6 and want_sim > 0.5):
                conflict = {
                    'type': 'duplicate',
                    'confidence': min(1.0, overall + 0.2),
                    'reason': f'High similarity: title={title_sim:.2f}, want={want_sim:.2f}'
                }

            # Check for SCOPE_OVERLAP: siblings with shared keywords
            elif data_a['story']['parent_id'] == data_b['story']['parent_id'] and data_a['story']['parent_id']:
                shared_tokens = data_a['all_tokens'] & data_b['all_tokens']
                if len(shared_tokens) >= 5 or desc_sim > 0.35:
                    conflict = {
                        'type': 'scope_overlap',
                        'confidence': min(1.0, desc_sim + 0.3),
                        'reason': f'Siblings share {len(shared_tokens)} keywords: {list(shared_tokens)[:5]}'
                    }

            # Check for COMPETING: similar want, different approach
            elif want_sim > 0.4 and desc_sim < 0.4:
                conflict = {
                    'type': 'competing',
                    'confidence': want_sim,
                    'reason': f'Similar want ({want_sim:.2f}) but different description ({desc_sim:.2f})'
                }

            if conflict:
                conflicts.append({
                    'story_a': {'id': id_a, 'title': data_a['story']['title'], 'status': data_a['story']['status']},
                    'story_b': {'id': id_b, 'title': data_b['story']['title'], 'status': data_b['story']['status']},
                    'conflict_type': conflict['type'],
                    'confidence': round(conflict['confidence'], 2),
                    'reason': conflict['reason'],
                    'title_similarity': round(title_sim, 2),
                    'want_similarity': round(want_sim, 2)
                })

    # Sort by confidence descending
    conflicts.sort(key=lambda x: x['confidence'], reverse=True)
    return conflicts

# Load stories
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT
        s.id, s.title, s.description, s.status,
        (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
    FROM story_nodes s
    WHERE s.status NOT IN ('rejected', 'archived', 'deprecated', 'infeasible')
    ORDER BY s.id
''').fetchall()]
conn.close()

# Run detection
conflicts = detect_conflicts(stories)

print(json.dumps({
    'total_stories': len(stories),
    'conflicts_found': len(conflicts),
    'conflicts': conflicts
}, indent=2))
"
```

### Step 3: Output Conflict Report

Format results for human review:

```
CONFLICT DETECTION REPORT
=========================

Stories scanned: [N]
Conflicts found: [M]

HIGH CONFIDENCE (>0.7):
-----------------------
1. [DUPLICATE] ID_A vs ID_B (confidence: 0.85)
   - Story A: "Title A" (status)
   - Story B: "Title B" (status)
   - Reason: High similarity: title=0.70, want=0.65

MEDIUM CONFIDENCE (0.5-0.7):
----------------------------
[...]

LOW CONFIDENCE (<0.5):
----------------------
[...]

RECOMMENDED ACTIONS:
- Review HIGH confidence duplicates for merge/rejection
- Check SCOPE_OVERLAP siblings for clearer boundaries
- Validate COMPETING stories have distinct approaches
```

## Confidence Thresholds

| Confidence | Meaning | Recommended Action |
|------------|---------|-------------------|
| > 0.7 | High - likely true conflict | Review immediately |
| 0.5 - 0.7 | Medium - possible conflict | Investigate further |
| < 0.5 | Low - flagged for awareness | Note but may be false positive |

## Integration Points

### Pre-Story-Writing Check

Before story-writing skill generates new stories, run conflict detection on the target parent's existing children to avoid generating duplicates.

### Post-Generation Validation

After new stories are created, run conflict detection to flag any newly introduced conflicts.

### CI Integration

```yaml
- name: Check for story conflicts
  run: |
    # Run conflict detection and fail if high-confidence duplicates found
    python -c "
    # [conflict detection code]
    conflicts = detect_conflicts(stories)
    high_conf = [c for c in conflicts if c['confidence'] > 0.7]
    if high_conf:
        print(f'::warning::Found {len(high_conf)} high-confidence conflicts')
        for c in high_conf:
            print(f\"  - {c['conflict_type']}: {c['story_a']['id']} vs {c['story_b']['id']}\")
    "
```

## Limitations

- **Lightweight approach**: Uses word-based Jaccard similarity, not semantic embeddings
- **False positives**: Similar vocabulary doesn't always mean duplicate intent
- **Context blind**: Cannot understand nuanced differences in approaches
- **Language dependent**: Optimized for English user stories

## References

- **Database:** `.claude/data/story-tree.db`
- **Schema:** `.claude/skills/story-tree/references/schema.sql`
- **Problem Space Schema:** `ai_docs/Orchestrator/2025-12-16-Problem-Space-Schema.md` (heavyweight alternative)
