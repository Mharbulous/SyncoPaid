# Create Lightweight Conflict Detection Skill

## Task

Create a skill that detects duplicate and overlapping stories in the story-tree database before new concepts are proposed for user approval.

## Context

The story-tree orchestrator generates stories autonomously via GitHub Actions. Stories are generated per-node with only sibling context visible to Claude. This creates a blind spot for **cross-branch duplicates** where similar features get conceived under different parent nodes.

A detailed Problem Space Detection schema was designed but is heavyweight for current scale. Instead, create a **lightweight pre-generation check** that can be invoked before proposing new concepts.

## Deliverable

A skill at `.claude/skills/conflict-detection/SKILL.md` that:

1. Takes a proposed story (title + description) as input
2. Compares against all `concept`/`approved`/`planned` stories in database
3. Returns potential conflicts with confidence scores
4. Flags: duplicates, scope overlaps, competing approaches

## Key Files

| File | Purpose |
|------|---------|
| `.claude/data/story-tree.db` | Story database (SQLite) |
| `.claude/skills/story-tree/references/schema.sql` | Database schema v3 |
| `.claude/skills/story-writing/SKILL.md` | Example skill structure |
| `ai_docs/Orchestrator/2025-12-16-Problem-Space-Schema.md` | Full schema (reference for conflict types, NOT to implement) |

## Red Herrings (Do Not Read)

- `.claude/data/insert_stories.py` - Screenshot deduplication, not story deduplication
- `src/syncopaid/screenshot.py` - dHash for images, not text
- `ai_docs/Reports/2025-12-17-story-conflict-analysis.md` - Contains test answers
- `ai_docs/Optimization-testing/*conflict*` - Contains test answers

## Technical Approach

Keep it simple. No embeddings or ML for v1.

**Recommended technique:** Keyword/phrase extraction + overlap scoring

```python
# Pseudocode
def check_conflicts(proposed_title, proposed_description):
    # 1. Extract key phrases from proposed story
    # 2. Query all active stories from database
    # 3. For each story, compute overlap score:
    #    - Title word overlap (Jaccard similarity)
    #    - Description keyword overlap
    #    - User role match ("As a lawyer...")
    # 4. Return stories above threshold with conflict type
```

**Conflict types to detect:**
- `duplicate`: Same feature, different wording (high title+description overlap)
- `scope_overlap`: One story subsumes another (partial description match)
- `competing`: Same problem, different approach (same "I want", different acceptance criteria)

## Research References

- **S3CDA algorithm**: Two-phase conflict detection using sentence embeddings + cosine similarity - [arXiv paper](https://arxiv.org/html/2206.13690)
- **ADRs**: Architecture Decision Records for tracking approach choices - [adr.github.io](https://adr.github.io/)
- **Jaccard similarity**: Simple set-based text similarity - standard approach for keyword overlap

## Constraints

- Python sqlite3 module only (no CLI)
- No external dependencies (no numpy, sklearn, sentence-transformers)
- Must run in CI environment (GitHub Actions)
- Max 3 seconds execution time

## Output Format

```
Conflict Check Results for: "[Proposed Title]"

POTENTIAL CONFLICTS:
  1. [story_id] (duplicate, 85% confidence)
     Title: [existing title]
     Reason: High title overlap + same user role

  2. [story_id] (scope_overlap, 62% confidence)
     Title: [existing title]
     Reason: Proposed story subsumes existing acceptance criteria

NO CONFLICTS with 45 other active stories.
```

## Success Criteria

- Detects obvious duplicates (same feature, different branch)
- Flags scope overlaps with reasonable accuracy
- Low false positive rate (don't flag every vaguely related story)
- Fast enough for CI integration

## Validation

After creating the skill, run it against the full database to find all potential conflicts. Report findings to user for manual review.
