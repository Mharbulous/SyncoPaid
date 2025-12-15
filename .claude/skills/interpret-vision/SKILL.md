---
name: interpret-vision
description: Use when user says "interpret vision", "update vision", "what's my vision", "show vision", "vision summary", "what am I building", "project direction", or asks about the overall direction or intent of the project - generates two markdown files summarizing the user's vision based on approved story nodes (what the vision IS) and rejected story nodes with notes (what the vision is NOT).
---

# Interpret Vision - Vision Synthesis Skill

## Purpose

Synthesize the user's **product vision** from the story-tree database by analyzing:
- **Approved stories** → What the user wants to build (`user-vision.md`)
- **Rejected stories with notes** → What the user explicitly doesn't want (`user-anti-vision.md`)

This creates living documentation that evolves as users approve/reject more stories.

## Output Files

| File | Location | Content |
|------|----------|---------|
| `user-vision.md` | `ai_docs/user-vision.md` | Concise bullet-point summary of what the user is building |
| `user-anti-vision.md` | `ai_docs/user-anti-vision.md` | Bullet-point summary of what the vision explicitly excludes |

## When to Use

- User explicitly asks about vision or project direction
- Before generating new stories (to ensure alignment)
- After significant batch of approvals/rejections
- When onboarding to understand project intent

## When NOT to Use

- No approved or rejected stories exist yet
- User wants to manually write vision documentation
- Just starting a fresh project (use story-tree first)

## Workflow

**CRITICAL:** For token efficiency, spawn TWO parallel agents using the Task tool. Each agent handles one vision file independently.

### Step 1: Check Prerequisites

Verify story-tree database exists and has relevant data:

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute(\"SELECT COUNT(*) FROM story_nodes WHERE status = 'approved'\")
approved = cursor.fetchone()[0]

cursor.execute(\"SELECT COUNT(*) FROM story_nodes WHERE status = 'rejected' AND notes IS NOT NULL AND notes != ''\")
rejected_with_notes = cursor.fetchone()[0]

print(f'Approved stories: {approved}')
print(f'Rejected stories with notes: {rejected_with_notes}')
conn.close()
"
```

If both counts are 0, inform user there's insufficient data to generate vision summaries.

### Step 2: Spawn Parallel Vision Agents

Use the Task tool to spawn TWO agents simultaneously:

#### Agent 1: Vision Synthesis (user-vision.md)

```
Prompt for Agent 1:
---
You are synthesizing the user's product vision from approved story nodes.

DATABASE: .claude/data/story-tree.db
OUTPUT FILE: ai_docs/user-vision.md

STEPS:
1. Read existing ai_docs/user-vision.md if it exists (to preserve context)
2. Query all approved stories from the database:

   python -c "
   import sqlite3
   conn = sqlite3.connect('.claude/data/story-tree.db')
   cursor = conn.cursor()
   cursor.execute('''
       SELECT id, title, description, notes FROM story_nodes
       WHERE status = 'approved'
       ORDER BY id
   ''')
   for row in cursor.fetchall():
       print(f'=== {row[0]}: {row[1]} ===')
       print(row[2])
       if row[3]: print(f'Notes: {row[3]}')
       print()
   conn.close()
   "

3. Analyze the approved stories to identify:
   - Core product purpose
   - Target user persona
   - Key capabilities being built
   - Underlying values and priorities

4. Write ai_docs/user-vision.md with this structure:

   # Product Vision

   ## What We're Building
   [1-2 sentence summary of the product]

   ## Target User
   [Who this is for]

   ## Core Capabilities
   - [Bullet point for each major capability area]
   - [Derived from approved story themes]

   ## Guiding Principles
   - [Values inferred from what's been approved]

   ---
   *Auto-generated from approved story nodes. Last updated: [timestamp]*

5. Return a brief summary of what you synthesized.
---
```

#### Agent 2: Anti-Vision Synthesis (user-vision-is-not.md)

```
Prompt for Agent 2:
---
You are synthesizing what the user's product vision explicitly EXCLUDES based on rejected stories.

DATABASE: .claude/data/story-tree.db
OUTPUT FILE: ai_docs/user-anti-vision.md

STEPS:
1. Read existing ai_docs/user-anti-vision.md if it exists (to preserve context)
2. Query all rejected stories WITH notes from the database:

   python -c "
   import sqlite3
   conn = sqlite3.connect('.claude/data/story-tree.db')
   cursor = conn.cursor()
   cursor.execute('''
       SELECT id, title, description, notes FROM story_nodes
       WHERE status = 'rejected' AND notes IS NOT NULL AND notes != ''
       ORDER BY id
   ''')
   for row in cursor.fetchall():
       print(f'=== {row[0]}: {row[1]} ===')
       print(row[2])
       print(f'REJECTION REASON: {row[3]}')
       print()
   conn.close()
   "

3. Analyze the rejection notes to identify:
   - Explicit exclusions (what the product won't do)
   - Anti-patterns the user wants to avoid
   - Features deemed unnecessary (YAGNI)
   - Philosophical boundaries

4. Write ai_docs/user-anti-vision.md with this structure:

   # What This Product is NOT

   ## Explicit Exclusions
   - [Feature/capability explicitly rejected]
     - *Reason: [from rejection notes]*

   ## Anti-Patterns to Avoid
   - [Pattern the user doesn't want]

   ## YAGNI Items
   - [Features marked as unnecessary complexity]

   ## Philosophical Boundaries
   - [Higher-level principles about what NOT to build]

   ---
   *Auto-generated from rejected story nodes. Last updated: [timestamp]*

5. Return a brief summary of what exclusions you identified.
---
```

### Step 3: Report Results

After both agents complete, summarize:

```markdown
# Vision Files Updated

## user-vision.md
[Summary from Agent 1]

## user-vision-is-not.md
[Summary from Agent 2]

Files location: `ai_docs/`
```

## Example Execution

When user says "interpret vision" or "update vision":

```
1. Check database has approved/rejected stories ✓
2. Spawn Agent 1 (vision synthesis) and Agent 2 (anti-vision synthesis) in PARALLEL
3. Wait for both to complete
4. Report summaries to user
```

## Important Notes

- **Always spawn both agents in parallel** - do not run sequentially
- **Preserve existing content** - agents should read existing files first to maintain context
- **Only include rejected stories with notes** - stories without rejection reasons don't inform the anti-vision
- **Use Python sqlite3** - never use sqlite3 CLI (see story-tree skill for details)

## References

- Story-tree database: `.claude/data/story-tree.db`
- Story-tree skill: `.claude/skills/story-tree/SKILL.md`
