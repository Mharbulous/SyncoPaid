# Create Lightweight Conflict Detection Skill

## Task

Create a skill that detects duplicate and overlapping stories in the story-tree database before new concepts are proposed for user approval.

## Context

The story-tree orchestrator generates stories autonomously via GitHub Actions. A detailed Problem Space Detection schema was designed (`ai_docs/Orchestrator/2025-12-16-Problem-Space-Schema.md`) but is heavyweight for current scale. Instead, create a **lightweight alternative**.

## Deliverable

A skill at `.claude/skills/conflict-detection/SKILL.md` that:

1. Scans stories in the database
2. Identifies potential conflicts between story pairs
3. Returns findings with confidence scores

## Conflict Types to Detect

- `duplicate`: Essentially the same story
- `scope_overlap`: One story subsumes or partially covers another
- `competing`: Same problem, incompatible approaches

## Key Files

| File | Purpose |
|------|---------|
| `.claude/data/story-tree.db` | Story database (SQLite) |
| `.claude/skills/story-tree/references/schema.sql` | Database schema v3 |
| `.claude/skills/story-writing/SKILL.md` | Example skill structure |
| `ai_docs/Orchestrator/2025-12-16-Problem-Space-Schema.md` | Reference for conflict type definitions |

## Do Not Read

- `ai_docs/Reports/2025-12-17-story-conflict-analysis.md` - Contains test answers
- `ai_docs/Optimization-testing/*conflict*` - Contains test answers

## Constraints

- Python sqlite3 module only (no CLI)
- No external dependencies (no numpy, sklearn, sentence-transformers)
- Must run in CI environment (GitHub Actions)

## Success Criteria

- Detects duplicates
- Flags scope overlaps
- Low false positive rate
- Fast execution

## Validation

After creating the skill:

1. **Full database scan**: Compare existing story pairs to find conflicts
2. **Report findings**: Present detected conflicts with IDs, types, and confidence scores
3. **Await feedback**: User will provide test cases for accuracy assessment and iteration
