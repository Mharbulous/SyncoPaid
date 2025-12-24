# Gap Analysis - Evidence-Based Story Discovery

Identify missing functionality by analyzing commits, existing stories, and project goals.

---

## Gap Types

| Type | Description | Example |
|------|-------------|---------|
| **Functional** | Missing capability in parent scope | Parent is "User Authentication" but no "Password Reset" story exists |
| **Pattern** | Commits exist without corresponding stories | 5 commits reference "caching" but no caching story |
| **User Journey** | Incomplete workflow | "Create Account" and "Delete Account" exist, but no "Update Profile" |
| **Technical** | Infrastructure gap | App has API but no rate limiting or error handling stories |

---

## Analysis Workflow

### Step 1: Gather Evidence

#### Recent Commits (30 days)
```python
python -c "
import subprocess
result = subprocess.run(['git', 'log', '--since=30 days ago',
    '--pretty=format:%h|%ai|%s', '--no-merges'], capture_output=True, text=True)
print(result.stdout)
"
```

#### Existing Children of Target Node
```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
children = [dict(row) for row in conn.execute('''
    SELECT s.id, s.title, s.description, COALESCE(s.disposition, s.hold_reason, s.stage) as status
    FROM story_nodes s
    JOIN story_paths p ON s.id = p.descendant_id
    WHERE p.ancestor_id = ? AND p.depth = 1
''', ('TARGET_PARENT_ID',)).fetchall()]
print(json.dumps(children, indent=2))
conn.close()
"
```

### Step 2: Match Commits to Scope

For each commit, determine if it relates to the target parent node:
- Extract keywords from commit message
- Compare against parent node title/description
- Group related commits together

### Step 3: Identify Gaps

For each gap type, scan for missing coverage:

**Functional gaps:**
- What capabilities does the parent scope imply?
- Which are missing from existing children?

**Pattern gaps:**
- Which commit clusters have no corresponding story?
- Are there repeated changes to files with no story coverage?

**User journey gaps:**
- What workflows does a user perform in this scope?
- Are there missing steps in any workflow?

**Technical gaps:**
- What infrastructure does the feature require?
- Are there missing cross-cutting concerns (logging, error handling, security)?

---

## Goals-Aware Filtering

When goals files exist, apply additional filtering:

### Load Goals
```python
python -c "
import os, json
result = {}
for key, path in [('goals', '.claude/data/goals/goals.md'), ('non_goals', '.claude/data/goals/non-goals.md')]:
    if os.path.exists(path):
        with open(path) as f: result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

### Apply Filters

| Check | Action |
|-------|--------|
| Gap aligns with core capabilities | ✓ Include |
| Gap conflicts with non-goals | ✗ Reject with reason |
| Gap is speculative (no commits, not in goals) | ✗ Reject as ungrounded |
| Gap extends scope beyond parent | ✗ Reject as scope creep |

### Rejection Tracking

When rejecting a gap, record the reason for the output report:
- "Conflicts with non-goal: [specific non-goal]"
- "Ungrounded: no commit evidence and not in goals"
- "Scope creep: extends beyond parent scope"

---

## Output Format

After analysis, produce a gap summary:

```markdown
## Gap Analysis for [Parent ID]: [Parent Title]

### Commits Analyzed
- [N] commits in last 30 days
- [M] related to this scope

### Gaps Identified
1. **[Gap Type]**: [Description]
   - Evidence: [commits or reasoning]
   - Proposed story: [brief description]

2. **[Gap Type]**: [Description]
   - Evidence: [commits or reasoning]
   - Proposed story: [brief description]

### Gaps Rejected
- [Description]: [rejection reason]
```

---

## Limits

- **Max 3 gaps per invocation** (prevents scope explosion)
- **Max 1 gap per node when batching** (total max 2 stories)
- Only gaps with evidence (commits) or clear functional necessity
