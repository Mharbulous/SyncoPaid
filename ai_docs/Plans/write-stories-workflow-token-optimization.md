# Write-Stories Workflow Token Optimization Plan

## Problem Statement

The `write-stories.yml` GitHub Action workflow consumed **~43,000 tokens** (subagent peak) and cost **$0.79** for a single run that generated only 1 story. Analysis of the December 16, 2025 execution logs identified significant inefficiencies that can reduce token usage by an estimated 40-50%.

## Current Token Breakdown

| Phase | Tokens | Notes |
|-------|--------|-------|
| Initial system context | 20,767 | CLAUDE.md, system prompts |
| Failed `/write-stories` command | +500 | Wrong command name |
| Command discovery (Glob + Read) | +700 | Finding correct command |
| Subagent spawn + SKILL.md read | +14,000 | Full 334-line skill file |
| TodoWrite overhead (9 calls) | +1,500 | Both parent and subagent |
| Python escaping failures (3x) | +600 | Retry attempts |
| Sequential DB operations (8 scripts) | +3,000 | Separate Python scripts |
| Full tree visualization | +500 | 87-node tree output |
| **Total** | **~41,500** | Subagent peak: 43,337 |

## Identified Inefficiencies

### 1. Wrong Slash Command Name (Est. -1,200 tokens)

**Issue**: Workflow prompt says `/write-stories` but the command is `/generate-stories` (or `/write-story`).

**Evidence** from log:
```
❌ Error: <tool_use_error>Unknown slash command: write-stories</tool_use_error>
```

This triggered:
- Failed SlashCommand call (+300 tokens)
- Glob search for commands (+200 tokens)
- Read of generate-stories.md (+400 tokens)
- Second SlashCommand call (+300 tokens)

**Location**: `.github/workflows/write-stories.yml` line 51, 60-61

**Fix**: Update workflow prompt to use correct command name `/generate-stories`.

### 2. Excessive TodoWrite Usage (Est. -1,500 tokens)

**Issue**: 9 TodoWrite calls total across parent agent (2) and subagent (7) for predictable automated workflow.

**Evidence** from log:
- Parent: 2 TodoWrite calls for 2-item list
- Subagent: 7 TodoWrite calls for 6-item list, updating status one at a time

**Fix**: For automated YOLO-mode workflows, disable TodoWrite entirely or limit to 1 call at start.

**Implementation**: Add to workflow prompt:
```
Skip TodoWrite for this automated workflow - steps are predictable.
```

### 3. Python Inline Escaping Failures (Est. -600 tokens)

**Issue**: Three failed bash commands due to shell escaping of `!=` operator.

**Evidence** from log:
```
❌ Error: Exit code 1 File "<string>", line 8 if result.returncode \!= 0: ^ SyntaxError
```

Each failure wastes ~200 tokens on error output + retry.

**Root Cause**: The workflow's bash escaping doesn't handle `!=` in inline Python properly.

**Fix**: Create pre-written Python utility scripts instead of inline Python.

### 4. Large SKILL.md Files Read Every Run (Est. -3,500 tokens)

**Issue**: Subagent instructed to "Read the skill file at `.claude/skills/story-tree/SKILL.md`" (334 lines) and story-writing skill (602 lines) loaded.

**Evidence**: Combined skill files are ~940 lines of instructions, mostly not needed for CI automation.

**Fix Options**:
A. Create CI-optimized skill summaries (~80 lines each)
B. Create dedicated Python workflow script that handles all steps
C. Embed essential steps directly in command file, skip skill loading

**Recommended**: Option B - Create `.claude/scripts/story_workflow.py` with all logic.

### 5. Sequential Database Operations (Est. -2,000 tokens)

**Issue**: 8 separate Python scripts written to /tmp and executed:
1. Check if DB exists
2. Get lastAnalyzedCommit
3. Analyze git commits
4. Identify priority target
5. Check vision files
6. Gather context (parent + children)
7. Analyze relevant commits
8. Insert story + update metadata + get stats

**Fix**: Consolidate into single script with subcommands.

### 6. Redundant Subagent Delegation (Est. -2,500 tokens)

**Issue**: The generate-stories.md command delegates to a Task subagent which then:
- Reads SKILL.md
- Creates its own todo list
- Writes multiple Python scripts

**Evidence**: Subagent prompt alone is ~500 tokens, then it reads 334-line SKILL.md.

**Fix**: Replace subagent delegation with direct Python script execution.

### 7. Full Tree Visualization (Est. -500 tokens)

**Issue**: Generates 87-node tree visualization even for CI mode that only needs summary.

**Evidence** from log: Full tree output consumed ~1,500 characters.

**Fix**: Use `--summary` flag or skip visualization in CI mode.

## Implementation Tasks

### Task 1: Create Unified Story Workflow Script

Create `.claude/scripts/story_workflow.py`:

```python
#!/usr/bin/env python3
"""
Unified story generation workflow for CI automation.
Usage: python .claude/scripts/story_workflow.py [--max-stories N] [--ci]
"""
import sqlite3
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = '.claude/data/story-tree.db'

def get_last_commit():
    """Get last analyzed commit from metadata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM metadata WHERE key = 'lastAnalyzedCommit'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_new_commits(last_commit):
    """Get commits since last analysis."""
    if last_commit:
        result = subprocess.run(['git', 'cat-file', '-t', last_commit], capture_output=True)
        if result.returncode != 0:
            last_commit = None

    if last_commit:
        cmd = ['git', 'log', f'{last_commit}..HEAD', '--pretty=format:%h|%s', '--no-merges']
    else:
        cmd = ['git', 'log', '--since=30 days ago', '--pretty=format:%h|%s', '--no-merges']

    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line and '|' in line:
            hash_, msg = line.split('|', 1)
            commits.append({'hash': hash_, 'message': msg})
    return commits, result.stdout.split('\n')[0].split('|')[0] if result.stdout else last_commit

def find_priority_target():
    """Find under-capacity node prioritizing shallower nodes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.title, s.description, s.capacity,
            (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
            (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
            COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
                 JOIN story_nodes child ON sp.descendant_id = child.id
                 WHERE sp.ancestor_id = s.id AND sp.depth = 1
                 AND child.status IN ('implemented', 'ready'))) as effective_capacity
        FROM story_nodes s
        WHERE s.status NOT IN ('concept', 'broken', 'refine', 'rejected', 'wishlist', 'deprecated', 'archived', 'infeasible', 'legacy')
          AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
              COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
                   JOIN story_nodes child ON sp.descendant_id = child.id
                   WHERE sp.ancestor_id = s.id AND sp.depth = 1
                   AND child.status IN ('implemented', 'ready')))
        ORDER BY node_depth ASC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0], 'title': row[1], 'description': row[2],
            'capacity': row[3], 'child_count': row[4],
            'node_depth': row[5], 'effective_capacity': row[6]
        }
    return None

def get_node_context(node_id):
    """Get parent node and children context."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.id, s.title, s.description, s.status
        FROM story_nodes s
        JOIN story_paths sp ON s.id = sp.descendant_id
        WHERE sp.ancestor_id = ? AND sp.depth = 1
        ORDER BY s.id
    ''', (node_id,))
    children = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return children

def get_next_child_id(parent_id):
    """Get next available child ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id FROM story_nodes s
        JOIN story_paths sp ON s.id = sp.descendant_id
        WHERE sp.ancestor_id = ? AND sp.depth = 1
        ORDER BY CAST(SUBSTR(s.id, LENGTH(?) + 2) AS INTEGER) DESC
        LIMIT 1
    ''', (parent_id, parent_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        last_num = int(row[0].split('.')[-1])
        return f"{parent_id}.{last_num + 1}"
    return f"{parent_id}.1"

def get_stats():
    """Get tree statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM story_nodes')
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'implemented'")
    implemented = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM story_nodes WHERE status = 'concept'")
    concept = cursor.fetchone()[0]
    conn.close()
    return {'total': total, 'implemented': implemented, 'concept': concept}

def update_metadata(newest_commit):
    """Update lastUpdated and lastAnalyzedCommit."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))")
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', ?)", (newest_commit,))
    conn.commit()
    conn.close()

def main():
    ci_mode = '--ci' in sys.argv
    max_stories = 2  # Default for CI

    for i, arg in enumerate(sys.argv):
        if arg == '--max-stories' and i + 1 < len(sys.argv):
            max_stories = int(sys.argv[i + 1])

    # Step 1: Check prerequisites
    if not Path(DB_PATH).exists():
        print('ERROR: Database not found')
        sys.exit(1)

    # Step 2: Analyze commits
    last_commit = get_last_commit()
    commits, newest_commit = get_new_commits(last_commit)

    # Step 3: Find priority target
    target = find_priority_target()
    if not target:
        print('NO_CAPACITY: All nodes at capacity')
        sys.exit(0)

    # Step 4: Get context
    children = get_node_context(target['id'])
    next_id = get_next_child_id(target['id'])

    # Output context for Claude to generate story
    output = {
        'target': target,
        'children': children,
        'next_id': next_id,
        'commits_analyzed': len(commits),
        'newest_commit': newest_commit,
        'stats': get_stats()
    }

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
```

### Task 2: Create Story Insertion Script

Create `.claude/scripts/insert_story.py`:

```python
#!/usr/bin/env python3
"""Insert a story into the database."""
import sqlite3
import sys
import json

DB_PATH = '.claude/data/story-tree.db'

def insert_story(story_id, parent_id, title, description):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
        VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
    ''', (story_id, title, description))

    cursor.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        SELECT ancestor_id, ?, depth + 1
        FROM story_paths WHERE descendant_id = ?
        UNION ALL SELECT ?, ?, 0
    ''', (story_id, parent_id, story_id, story_id))

    conn.commit()
    conn.close()
    print(f'✓ Inserted story {story_id}')

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: insert_story.py <id> <parent_id> <title> <description>')
        sys.exit(1)
    insert_story(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
```

### Task 3: Update generate-stories.md Command

Replace `.claude/commands/generate-stories.md`:

```markdown
Generate user story concepts for nodes with capacity using pre-built workflow scripts.

## CI Mode (Automated)

When running in automated/YOLO mode (no user interaction):

1. **Run workflow script** to get target node context:
```bash
python .claude/scripts/story_workflow.py --ci
```

2. **If NO_CAPACITY**, exit successfully - nothing to generate.

3. **Generate story** based on the JSON output:
   - Use target node's description to identify gaps
   - Review existing children to avoid duplicates
   - Create ONE story in user story format (As a/I want/So that)

4. **Insert story** using:
```bash
python .claude/scripts/insert_story.py "<id>" "<parent_id>" "<title>" "<description>"
```

5. **Update metadata**:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.execute(\"INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', 'COMMIT_HASH')\")
conn.commit()
"
```

## Interactive Mode

For interactive use, invoke the `story-writing` skill which provides full context gathering and rich output.

## Output Format (CI)

```
✓ Generated 1 story for node [PARENT_ID]:
  - [STORY_ID]: [Title]
```
```

### Task 4: Update Workflow Prompt

Update `.github/workflows/write-stories.yml`:

```yaml
prompt: |
  REPO: ${{ github.repository }}
  MODE: Daily Story Generation (YOLO mode)

  Run automated story generation. Skip TodoWrite - steps are predictable.

  ## Steps

  1. Run: `python .claude/scripts/story_workflow.py --ci`
  2. If output is NO_CAPACITY, exit successfully
  3. Parse JSON output to get target node context
  4. Generate ONE user story based on target's description and gaps
  5. Insert using: `python .claude/scripts/insert_story.py <args>`
  6. Commit and push: `git add -A && git commit -m "stories: auto-generate $(date -u +'%Y-%m-%d')" && git push origin main`

  Story format: As a [role] / I want [capability] / So that [benefit] + Acceptance Criteria

  Constraints: Max 1 story per run. Status: concept. 30-minute timeout.
```

### Task 5: Remove Subagent Delegation

The current workflow uses Task tool to spawn a subagent that reads SKILL.md. With the new script approach:
- No subagent needed
- No SKILL.md reading needed
- Direct execution of optimized Python scripts

## Expected Results

| Optimization | Token Savings |
|--------------|---------------|
| Fix command name (no retry) | -1,200 |
| Skip TodoWrite | -1,500 |
| Pre-built scripts (no escaping errors) | -600 |
| Skip SKILL.md reads | -3,500 |
| Consolidated DB operations | -2,000 |
| No subagent delegation | -2,500 |
| Skip tree visualization | -500 |
| Shorter workflow prompt | -300 |
| **Total Estimated Savings** | **~12,100 tokens (29%)** |

**New estimated total**: ~29,000 tokens
**New estimated cost**: ~$0.55 per run (down from $0.79)

## Verification Plan

1. Create helper scripts (Tasks 1-2) and test locally
2. Update generate-stories.md (Task 3)
3. Test with `workflow_dispatch` trigger
4. Compare token usage in GitHub Actions logs
5. Update workflow prompt (Task 4) if scripts work
6. Monitor scheduled runs for one week

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Scripts may not handle edge cases | Include error handling, test with various DB states |
| Story quality may decrease without full skill context | Embed essential story format in workflow prompt |
| Breaking existing interactive mode | Keep story-writing skill for interactive use |
| Script path issues in CI | Use absolute paths, test in GitHub Actions environment |

## Implementation Order

1. **Task 1-2**: Create Python helper scripts (enables all other optimizations)
2. **Task 3**: Update generate-stories.md (low risk, improves both modes)
3. **Test**: Run workflow manually to verify
4. **Task 4**: Optimize workflow prompt (after confirming scripts work)
5. **Task 5**: Remove subagent delegation (final optimization)

## Comparison: Before vs After

### Before (Current)
```
Workflow → SlashCommand (wrong) → Glob → Read → SlashCommand →
  expand generate-stories.md → Task subagent →
    Read SKILL.md → 7x TodoWrite → 8x Python scripts to /tmp →
    3x escaping failures → Skill invocation → tree visualization
```

### After (Optimized)
```
Workflow → python story_workflow.py →
  generate story content → python insert_story.py →
  git commit/push
```

---
*Plan created: 2025-12-16*
*Based on analysis of write-stories.yml run from 2025-12-16 09:40*
