---
name: goal-synthesis
description: Use when user says "synthesize goals", "show goals", "what are my goals", "update goals", "show non-goals", "what am I building", "project direction", or asks about the overall direction or intent of the project - generates two markdown files summarizing the user's goals based on approved story nodes (what the goals ARE) and rejected story nodes with notes (what the non-goals ARE).
---

# Goal Synthesis Skill

Generate `{today}-goals.md` and `{today}-non-goals.md` in `ai_docs/Xstory/`.

## Workflow

### Step 1: Check Prerequisites

```bash
python .claude/scripts/story_tree_helpers.py prereq
```

Returns JSON with: `today`, `db_exists`, `approved_count`, `rejected_with_notes_count`, `goals_exists`, `non_goals_exists`.

**Exit early if**:
- Both files exist for today, OR
- No story data (`approved_count` = 0 AND `rejected_with_notes_count` = 0)

### Step 2: Spawn Parallel Agents

Launch TWO Task agents simultaneously (use haiku model for both):

**Agent 1 (goals)** - Only if `goals_exists` is false:
```
Query approved stories: python .claude/scripts/story_tree_helpers.py approved

Read most recent ai_docs/Xstory/*-goals.md to preserve context.

Write ai_docs/Xstory/{today}-goals.md with sections:
- What We're Building (1-2 sentences)
- Target User
- Core Capabilities (bullets)
- Guiding Principles (bullets)
- Footer: *Auto-generated from approved story nodes. Last updated: {timestamp}*

Return brief summary.
```

**Agent 2 (non-goals)** - Only if `non_goals_exists` is false:
```
Query rejected stories: python .claude/scripts/story_tree_helpers.py rejected

Read most recent ai_docs/Xstory/*-non-goals.md to preserve context.

Write ai_docs/Xstory/{today}-non-goals.md with sections:
- Explicit Exclusions (with rejection reasons)
- Anti-Patterns to Avoid
- YAGNI Items
- Philosophical Boundaries
- Footer: *Auto-generated from rejected story nodes. Last updated: {timestamp}*

Return brief summary.
```

**Important**: Replace `{today}` with the date from Step 1 prerequisites (format: YYYY-MM-DD).

### Step 3: Report Results

Summarize what was generated, listing created files.

## Key Rules

- **Spawn agents in parallel** - never sequentially
- **Use Python sqlite3** - not sqlite3 CLI
- **Include rejection reasons** in non-goals bullets
- **Read existing files first** to preserve accumulated context
