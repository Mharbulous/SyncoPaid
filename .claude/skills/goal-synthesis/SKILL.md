---
name: goal-synthesis
description: Use when user says "synthesize goals", "show goals", "what are my goals", "update goals", "show non-goals", "what am I building", "project direction", or asks about the overall direction or intent of the project - generates two markdown files summarizing the user's goals based on approved story nodes (what the goals ARE) and rejected story nodes with notes (what the non-goals ARE).
---

# Goal Synthesis Skill

Generate `{today}-goals.md` and `{today}-non-goals.md` in `.claude/data/goals/`.

## Workflow

### Step 1: Check Prerequisites

```bash
python .claude/scripts/story_tree_helpers.py prereq
```

**Exit early if:**
- Both files exist for today, OR
- No story data (`approved_count` = 0 AND `rejected_with_notes_count` = 0)

### Step 2: Spawn Parallel Agents

Launch TWO Task agents simultaneously (haiku model):

**Agent 1 (goals)** - Only if `goals_exists` is false:
- Query: `python .claude/scripts/story_tree_helpers.py approved`
- Read most recent `.claude/data/goals/*-goals.md` for context
- Write `.claude/data/goals/{today}-goals.md` with sections: What We're Building, Target User, Core Capabilities, Guiding Principles, Footer with timestamp

**Agent 2 (non-goals)** - Only if `non_goals_exists` is false:
- Query: `python .claude/scripts/story_tree_helpers.py rejected`
- Read most recent `.claude/data/goals/*-non-goals.md` for context
- Write `.claude/data/goals/{today}-non-goals.md` with sections: Explicit Exclusions (with rejection reasons), Anti-Patterns, YAGNI Items, Philosophical Boundaries, Footer with timestamp

**Critical:** Replace `{today}` with date from Step 1 (format: YYYY-MM-DD).

## Key Rules

- Spawn agents in parallel, never sequentially
- Use Python sqlite3 module, NOT sqlite3 CLI
- Include rejection reasons in non-goals bullets
- Read existing files first to preserve accumulated context
