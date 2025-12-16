---
name: visualization
description: Use when user says "visualize", "update vision", "what's my vision", "show vision", "vision summary", "what am I building", "project direction", or asks about the overall direction or intent of the project - generates two markdown files summarizing the user's vision based on approved story nodes (what the vision IS) and rejected story nodes with notes (what the vision is NOT).
---

# Visualization Skill

Generate `{today}-user-vision.md` and `{today}-user-anti-vision.md` in `ai_docs/Xstory/`.

## Workflow

### Step 1: Check Prerequisites

```bash
python .claude/scripts/story_tree_helpers.py prereq
```

Returns JSON with: `today`, `db_exists`, `approved_count`, `rejected_with_notes_count`, `vision_exists`, `anti_vision_exists`.

**Exit early if**:
- Both files exist for today, OR
- No story data (`approved_count` = 0 AND `rejected_with_notes_count` = 0)

### Step 2: Spawn Parallel Agents

Launch TWO Task agents simultaneously (use haiku model for both):

**Agent 1 (vision)** - Only if `vision_exists` is false:
```
Query approved stories: python .claude/scripts/story_tree_helpers.py approved

Read most recent ai_docs/Xstory/*-user-vision.md to preserve context.

Write ai_docs/Xstory/{today}-user-vision.md with sections:
- What We're Building (1-2 sentences)
- Target User
- Core Capabilities (bullets)
- Guiding Principles (bullets)
- Footer: *Auto-generated from approved story nodes. Last updated: {timestamp}*

Return brief summary.
```

**Agent 2 (anti-vision)** - Only if `anti_vision_exists` is false:
```
Query rejected stories: python .claude/scripts/story_tree_helpers.py rejected

Read most recent ai_docs/Xstory/*-user-anti-vision.md to preserve context.

Write ai_docs/Xstory/{today}-user-anti-vision.md with sections:
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
- **Include rejection reasons** in anti-vision bullets
- **Read existing files first** to preserve accumulated context
