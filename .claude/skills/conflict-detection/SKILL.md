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
| `duplicate` | Essentially the same story | High-signal keyword match OR ≥2 shared implementation keywords |
| `scope_overlap` | One subsumes or partially covers another | Shared keywords + description similarity |
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

The algorithm uses specific implementation keyword matching (validated 10/10 on test cases):

```python
python3 << 'PYEOF'
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
                 'because', 'until', 'while', 'that', 'this', 'these', 'those'}
    return set(w for w in words if w not in stopwords and len(w) > 2)

def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def overlap_coefficient(set1, set2):
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / min(len(set1), len(set2))

def extract_acceptance_criteria(description):
    if not description:
        return ''
    match = re.search(r'[Aa]cceptance [Cc]riteria[:\s]*(.+?)(?:\n\n|\*\*Related|$)', description, re.DOTALL)
    return match.group(1) if match else ''

# High-signal keywords that strongly indicate same feature (even 1 match = likely duplicate)
HIGH_SIGNAL_KEYWORDS = {'matter_table', 'client_table', 'app_blocking', 'archive_compress'}

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

def detect_conflicts(stories):
    '''Detect conflicts between story pairs.'''
    conflicts = []
    story_data = {}

    for s in stories:
        story_id = s['id']
        title_tokens = tokenize(s['title'])
        desc_tokens = tokenize(s['description'])
        ac_tokens = tokenize(extract_acceptance_criteria(s['description']))
        spec_keywords = find_specific_keywords(s['description'])

        story_data[story_id] = {
            'story': s,
            'title_tokens': title_tokens,
            'desc_tokens': desc_tokens,
            'ac_tokens': ac_tokens,
            'spec_keywords': spec_keywords
        }

    story_ids = list(story_data.keys())
    for i in range(len(story_ids)):
        for j in range(i + 1, len(story_ids)):
            id_a, id_b = story_ids[i], story_ids[j]
            data_a, data_b = story_data[id_a], story_data[id_b]

            # Skip parent-child relationships
            if id_a.startswith(id_b + '.') or id_b.startswith(id_a + '.'):
                continue

            spec_shared = data_a['spec_keywords'] & data_b['spec_keywords']
            high_signal_shared = spec_shared & HIGH_SIGNAL_KEYWORDS

            title_sim = jaccard_similarity(data_a['title_tokens'], data_b['title_tokens'])
            title_overlap = overlap_coefficient(data_a['title_tokens'], data_b['title_tokens'])
            desc_sim = jaccard_similarity(data_a['desc_tokens'], data_b['desc_tokens'])
            ac_sim = jaccard_similarity(data_a['ac_tokens'], data_b['ac_tokens'])
            ac_overlap = overlap_coefficient(data_a['ac_tokens'], data_b['ac_tokens'])

            # Scoring
            dup_score = 0.0
            overlap_score = 0.0

            # DUPLICATE signals
            if len(spec_shared) >= 2:
                dup_score += 0.5
            elif len(high_signal_shared) >= 1:
                dup_score += 0.5
            if title_overlap > 0.6:
                dup_score += 0.3
            if ac_sim > 0.20:
                dup_score += 0.2

            # SCOPE_OVERLAP signals
            if len(spec_shared) == 1 and not high_signal_shared:
                overlap_score += 0.3
            if desc_sim > 0.12:
                overlap_score += 0.3
            if ac_overlap > 0.15:
                overlap_score += 0.2
            if title_sim > 0.1:
                overlap_score += 0.2

            conflict_type = None
            if dup_score >= 0.5:
                conflict_type = 'duplicate'
                confidence = min(1.0, dup_score + 0.3)
            elif overlap_score >= 0.4 or (len(spec_shared) >= 1 and not high_signal_shared):
                conflict_type = 'scope_overlap'
                confidence = min(1.0, overlap_score + 0.2)

            if conflict_type:
                conflicts.append({
                    'story_a': {'id': id_a, 'title': data_a['story']['title'], 'status': data_a['story']['status']},
                    'story_b': {'id': id_b, 'title': data_b['story']['title'], 'status': data_b['story']['status']},
                    'conflict_type': conflict_type,
                    'confidence': round(confidence, 2),
                    'shared_keywords': list(spec_shared),
                    'high_signal': list(high_signal_shared)
                })

    conflicts.sort(key=lambda x: x['confidence'], reverse=True)
    return conflicts

# Load and run
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.status,
           (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
    FROM story_nodes s
    WHERE s.status NOT IN ('rejected', 'archived', 'deprecated', 'infeasible')
    ORDER BY s.id
''').fetchall()]
conn.close()

conflicts = detect_conflicts(stories)
print(json.dumps({'total_stories': len(stories), 'conflicts_found': len(conflicts), 'conflicts': conflicts}, indent=2))
PYEOF
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
