# Visualization Workflow Token Optimization Plan

## Problem Statement

The `visualize.yml` GitHub Action workflow consumes ~32,000 tokens and costs $0.41 per run. Analysis of the December 16, 2025 execution logs identified several inefficiencies that can reduce token usage by an estimated 30-40%.

## Current Token Breakdown

| Phase | Tokens | Notes |
|-------|--------|-------|
| Initial system context | 20,786 | CLAUDE.md files, system prompts |
| Skill file injection | +3,699 | Full skill content as user message |
| Agent execution | +8,000 | Both agents + orchestration |
| **Total** | **32,376** | |

## Identified Inefficiencies

### 1. Redundant CLAUDE.md Read (Est. -750 tokens)

**Issue**: Workflow prompt instructs "Read CLAUDE.md for project conventions" but CLAUDE.md is already injected via system context at startup.

**Location**: `.github/workflows/visualize.yml` line 62

**Fix**: Remove instruction to read CLAUDE.md from workflow prompt.

### 2. Verbose Skill File (~250 lines → ~80 lines) (Est. -2,000 tokens)

**Issue**: The skill file contains:
- Duplicate SQL queries (same query appears in prerequisite check AND agent prompts)
- Full output format templates that Claude can infer
- Verbose agent prompts (~60 lines each)

**Location**: `.claude/skills/visualization/SKILL.md`

**Fixes**:
- Create shared Python helper script for database queries
- Reduce agent prompts to essential instructions only
- Remove redundant output format examples

### 3. Hardcoded Date Example Causes Agent Errors (Est. -1,500 tokens)

**Issue**: Agent prompts contain `2025-12-15` as example date. The non-goals agent created a file with wrong date, requiring 6 extra tool calls to detect and fix.

**Location**: Skill file lines 97, 159

**Fix**: Replace hardcoded date with `$(date +%Y-%m-%d)` or instruct agents to use Python's `date.today()`.

### 4. Sequential Prerequisite Checks (Est. -500 tokens)

**Issue**: Two separate Bash calls for:
1. Database story counts
2. File existence check

**Fix**: Combine into single Python script that outputs all prerequisite data.

### 5. TodoWrite Overhead for Automated Workflows (Est. -400 tokens)

**Issue**: 6 TodoWrite calls for a 4-item predictable checklist. Each call serializes the full todo array.

**Fix**: For automated YOLO-mode workflows, reduce to 2 TodoWrite calls (start and end) or eliminate entirely.

### 6. Agent Prompt Duplication

**Issue**: When Task tool spawns agents, the full prompt appears in the conversation as a user message, then again in the agent's context.

**Fix**: Use more concise agent prompts focused on the unique task, referencing shared conventions.

## Implementation Tasks

### Task 1: Create Shared Database Helper Script

Create `.claude/scripts/story_tree_helpers.py`:

```python
#!/usr/bin/env python3
"""Helper script for story-tree database operations."""
import sqlite3
import os
import json
from datetime import date

DB_PATH = '.claude/data/story-tree.db'
XSTORY_DIR = 'ai_docs/Xstory'

def get_prerequisites():
    """Return all prerequisite data in one call."""
    today = date.today().strftime('%Y-%m-%d')

    result = {
        'today': today,
        'db_exists': os.path.exists(DB_PATH),
        'approved_count': 0,
        'rejected_with_notes_count': 0,
        'vision_exists': os.path.exists(f'{XSTORY_DIR}/{today}-non-goals.md'),
        'anti_vision_exists': os.path.exists(f'{XSTORY_DIR}/{today}-user-non-goals.md'),
    }

    if result['db_exists']:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'approved'")
        result['approved_count'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'rejected' AND notes IS NOT NULL AND notes != ''")
        result['rejected_with_notes_count'] = cursor.fetchone()[0]
        conn.close()

    print(json.dumps(result, indent=2))
    return result

def get_approved_stories():
    """Output approved stories for vision synthesis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, description, notes FROM story_nodes
        WHERE status = 'approved' ORDER BY id
    ''')
    for row in cursor.fetchall():
        print(f'=== {row[0]}: {row[1]} ===')
        print(row[2])
        if row[3]: print(f'Notes: {row[3]}')
        print()
    conn.close()

def get_rejected_stories():
    """Output rejected stories with notes for non-goals synthesis."""
    conn = sqlite3.connect(DB_PATH)
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

if __name__ == '__main__':
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'prereq'
    {'prereq': get_prerequisites, 'approved': get_approved_stories, 'rejected': get_rejected_stories}[cmd]()
```

### Task 2: Optimize Workflow Prompt

Update `.github/workflows/visualize.yml` prompt section:

```yaml
prompt: |
  MODE: Daily Visualization Update (autonomous)

  Execute /visualize to generate vision documentation from story-tree database.

  YOLO mode behaviors:
  - No approval steps - complete autonomously
  - Commit directly with message: "docs: auto-update visualization YYYY-MM-DD"
  - Push to main branch

  Git workflow: git checkout main && git pull && git add -A && git commit && git push

  If no story data exists, exit without commits.
```

**Removed**:
- CLAUDE.md read instruction (already in context)
- Verbose git command examples (Claude knows git)
- Redundant constraint explanations

### Task 3: Optimize Skill File

Reduce `.claude/skills/visualization/SKILL.md` to essential instructions:

```markdown
---
name: visualization
description: Generate vision docs from story-tree database (approved → vision, rejected → non-goals)
---

# Visualization Skill

Generate `YYYY-MM-DD-non-goals.md` and `YYYY-MM-DD-user-non-goals.md` in `ai_docs/Xstory/`.

## Workflow

### Step 1: Check Prerequisites
```bash
python .claude/scripts/story_tree_helpers.py prereq
```

If both files exist for today OR no story data, exit early.

### Step 2: Spawn Parallel Agents

Launch TWO Task agents simultaneously (use haiku model):

**Agent 1 (vision)**: Query approved stories with `python .claude/scripts/story_tree_helpers.py approved`, synthesize into vision doc with sections: What We're Building, Target User, Core Capabilities, Guiding Principles.

**Agent 2 (non-goals)**: Query rejected stories with `python .claude/scripts/story_tree_helpers.py rejected`, synthesize into non-goals doc with sections: Explicit Exclusions, Anti-Patterns, YAGNI Items, Philosophical Boundaries.

Both agents should read the most recent existing file first to preserve context.

### Step 3: Report Results
Summarize what was generated.
```

### Task 4: Update Workflow to Skip TodoWrite

Add to workflow prompt:
```
Skip TodoWrite for this automated workflow - steps are predictable.
```

## Expected Results

| Optimization | Token Savings |
|--------------|---------------|
| Remove CLAUDE.md read | -750 |
| Shorter skill file | -2,000 |
| Fix date bug (no recovery work) | -1,500 |
| Combined prerequisites | -500 |
| Skip TodoWrite | -400 |
| Shorter workflow prompt | -300 |
| **Total Estimated Savings** | **~5,450 tokens (17%)** |

**New estimated total**: ~27,000 tokens
**New estimated cost**: ~$0.35 per run

## Verification

After implementation, run the workflow manually (`workflow_dispatch`) and compare:
- Total token count
- Execution time
- Cost

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Helper script path issues in CI | Test with `workflow_dispatch` before relying on schedule |
| Agents produce lower quality with shorter prompts | Include essential format requirements, test output quality |
| Breaking existing functionality | Implement incrementally, test each change |

## Implementation Order

1. Create helper script (Task 1) - low risk, enables other optimizations
2. Fix date bug in skill file - prevents wasted recovery work
3. Optimize skill file (Task 3) - largest token savings
4. Optimize workflow prompt (Task 2)
5. Disable TodoWrite for automated runs (Task 4)

---
*Plan created: 2025-12-16*
