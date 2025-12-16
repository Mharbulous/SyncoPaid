---
name: story-writing
description: Use when user says "brainstorm stories", "generate story ideas", "brainstorm features", "create stories for [node]", or asks for new story ideas - FIRST refines any existing stories with status='refine' before generating new stories. Then generates evidence-based user stories for nodes with capacity based on git commit analysis, existing children, and gap analysis. Works with story-tree database to create concept stories with proper user story format and acceptance criteria.
---

# Story Writing - Evidence-Based Story Generator

Generate user stories grounded in git commits and gap analysis.

**Database:** `.claude/data/story-tree.db`

**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## Priority Order

1. **FIRST:** Refine any stories with `status='refine'`
2. **THEN:** Generate new stories for target node

## Multi-Node Batching

When given multiple node IDs (e.g., "Generate stories for nodes: 1.2, 1.3"):
- Perform goals check and git analysis ONCE (shared context)
- Loop through nodes for context/gap/generation
- Max 1 story per node when batching, total max 2 stories
- Single combined output

Token savings: ~2,800 tokens per additional node.

## Workflow

### Step 0: Check for Stories Needing Refinement

```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
stories = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, s.status, s.notes,
           (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
    FROM story_nodes s WHERE s.status = 'refine' ORDER BY s.created_at
''').fetchall()]
print(json.dumps({'count': len(stories), 'stories': stories}, indent=2))
conn.close()
"
```

**If `refine` stories exist:** Process each one:
1. Identify issues (vague criteria, missing evidence, too broad, unclear role)
2. Rework with quality standards
3. Update to `status='concept'`

**Only proceed to new story generation AFTER all `refine` stories are processed.**

### Step 0a: Check Goals Files

```python
python -c "
import os, json
result = {}
for key, path in [('goals', 'ai_docs/goals.md'), ('non_goals', 'ai_docs/non-goals.md')]:
    result[f'has_{key}'] = os.path.exists(path)
    if result[f'has_{key}']:
        with open(path) as f: result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

If goals files exist, internalize:
- What the product IS (target user, core capabilities, guiding principles)
- What the product is NOT (explicit exclusions, anti-patterns)

If goals files don't exist, generate stories based purely on git commits and gaps.

### Step 1: Gather Parent Node Context

Query parent node and existing children using closure table joins.

### Step 2: Analyze Git Commits

```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

Match commits to parent node scope using keyword similarity.

### Step 3: Identify Gaps

**Gap types:** Functional, Pattern (commits without stories), User journey, Technical

**Goals-aware filtering (if files exist):**
- Cross-check against goals.md core capabilities
- Cross-check against non-goals.md exclusions
- Reject speculative features not grounded in goals OR commits

**Max 3 stories per invocation.**

### Step 4: Generate Stories

**Story ID format:** `[parent-id].[N]` (next available child number)

**Template:**
```markdown
### [ID]: [Title]

**As a** [specific user role from goals or codebase context]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context**: [Git commits or gaps that inform this story]
```

**Quality requirements:**
- Specific user role (not generic "user")
- Concrete, measurable capability
- Testable acceptance criteria
- Evidence from commits or clear functional gap
- Stories decompose parent scope (don't expand it)

### Step 5: Validate

**Check:**
- Each story has evidence (commits or gaps)
- User story format complete (As a/I want/So that)
- 3+ testable acceptance criteria
- No duplicates with existing children
- IDs follow hierarchy format
- Scope within parent description

**If goals files exist, also check:**
- Aligns with core capabilities
- No conflicts with non-goals exclusions
- Follows guiding principles

### Step 6: Insert Stories

Default `status: 'concept'`. Use `approved` only if user explicitly requested.

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')

# Insert story
conn.execute('''
    INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
    VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
''', ('NEW_ID', 'TITLE', 'DESCRIPTION'))

# Populate closure table
conn.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, ?, depth + 1 FROM story_paths WHERE descendant_id = ?
    UNION ALL SELECT ?, ?, 0
''', ('NEW_ID', 'PARENT_ID', 'NEW_ID', 'NEW_ID'))

conn.commit()
conn.close()
"
```

### Step 7: Output Report

Include: Goals status, context analysis, commits analyzed, gaps identified (with goals alignment), gaps rejected (with reasons), generated stories, next steps.

**CI mode output:**
```
✓ Generated [N] stories for node [PARENT_ID]:
  - [STORY_ID_1]: [Title 1]
  - [STORY_ID_2]: [Title 2]
```

## Key Rules

- **Always check `refine` status first** before generating new stories
- **Always check goals files** before generating (if they exist)
- Max 3 stories per invocation (max 1 per node when batching)
- Every story must reference commits OR specific gap
- Stories decompose parent scope, don't expand it
- Use specific user role from goals file or codebase context (not generic "user")

## References

- **Goals:** `ai_docs/goals.md`, `ai_docs/non-goals.md` (if they exist)
- **Database:** `.claude/data/story-tree.db`
- **Story Tree:** `.claude/skills/story-tree/SKILL.md`
- **Goal Synthesis:** `.claude/skills/goal-synthesis/SKILL.md`
