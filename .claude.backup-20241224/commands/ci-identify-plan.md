# Identify Plan - Match to Story Database

Identify a plan's corresponding story by matching it to the story database.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024_feature.md`)

---

## CONTEXT

This plan document does not contain a Story ID. Your task is to find the matching
story in the database by comparing the plan's content to story nodes.

## YOUR TASK

1. Read the plan document at `$ARGUMENTS` completely
2. Extract key information:
   - Title/description of what the plan implements
   - Key features or functionality
   - Any mentioned story references
3. Query the database at `.claude/data/story-tree.db` to find matching stories:
   - Compare plan content to story descriptions
   - Compare to story field (user story text)
   - Compare to success_criteria field
   - Look for similar keywords and concepts
4. If a confident match is found (>80% confidence), update the plan
5. If no match found, the plan should be blocked

## DATABASE SCHEMA

The story_nodes table has these columns:
- id: TEXT PRIMARY KEY (e.g., "7.6", "8.1.2")
- title: TEXT NOT NULL
- description: TEXT NOT NULL
- story: TEXT (user story text: "As a... I want... So that...")
- success_criteria: TEXT (acceptance criteria)
- stage: TEXT (concept, approved, planned, active, reviewing, verifying, implemented, ready, polish, released)
- hold_reason: TEXT (NULL if not held)
- disposition: TEXT (NULL if active in pipeline)

## SQL QUERY EXAMPLES

IMPORTANT: Do NOT use heredocs (<<EOF) for Python - they are blocked by security policy.
Instead, write Python code to a .py file and execute it:

```python
# Write this to a file like /tmp/query.py, then run: python3 /tmp/query.py
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
results = conn.execute('''
    SELECT id, title, description, story, success_criteria
    FROM story_nodes
    WHERE disposition IS NULL
      AND (title LIKE ? OR description LIKE ? OR story LIKE ?)
''', ('%keyword%', '%keyword%', '%keyword%')).fetchall()
for row in results:
    print(row)
```

Or use sqlite3 CLI directly (simpler for quick queries):
```bash
sqlite3 .claude/data/story-tree.db "SELECT id, title FROM story_nodes WHERE stage <> 'concept' AND disposition IS NULL"
```

## HOW TO UPDATE THE PLAN

If you find a matching story, add a Story ID line in the plan's header section.
Look for a metadata section near the top (often after the title) and add:

```markdown
**Story ID:** 7.6
```

Or if there's already a metadata table, add a row for Story ID.

## OUTPUT REQUIRED

**⚠️ CRITICAL: The output filename MUST be EXACTLY as specified below. Do NOT use "validate" - use "identify".**

Write a JSON file to `.claude/skills/story-execution/ci-identify-result.json`:

**FILENAME: `ci-identify-result.json`** (NOT ci-validate-result.json)

```json
{
  "validation_passed": true,
  "story_id": "7.6",
  "confidence": 0.85,
  "match_reason": "Brief explanation of why this story matches",
  "plan_updated": true,
  "block_reason": null
}
```

If no match found:
```json
{
  "validation_passed": false,
  "story_id": null,
  "confidence": 0,
  "match_reason": null,
  "plan_updated": false,
  "block_reason": "No matching story found in database"
}
```

## IMPORTANT

- Only update the plan file if you find a confident match (>80%)
- If you update the plan, set plan_updated=true
- If no match found, set validation_passed=false and provide block_reason

After writing the JSON, print a human-readable summary:

```
## Validation Result: [PASSED/FAILED]

**Plan:** [filename]
**Matched Story:** [story_id] - [story_title]
**Confidence:** [percentage]
**Reason:** [brief explanation]
```
