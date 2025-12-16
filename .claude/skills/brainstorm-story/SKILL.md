---
name: brainstorm-story
description: Use when user says "brainstorm stories", "generate story ideas", "brainstorm features", "create stories for [node]", or asks for new story ideas - generates evidence-based user stories for a given node based on git commit analysis, existing children, and gap analysis. Works with story-tree database to create concept stories with proper user story format and acceptance criteria.
---

# Brainstorm Story - Story Idea Generator

## Purpose

Generate **evidence-based user stories** for a given parent node by:
- Analyzing git commit history for implementation patterns
- Reviewing existing children to avoid duplication
- Identifying gaps in functionality
- Creating properly formatted user stories with acceptance criteria
- Inserting new stories as `concept` status (pending human approval)

**Design philosophy:** Stories should emerge from actual development patterns and real gaps, not speculation.

## When to Use

- User explicitly requests story generation for a specific node
- Called by `story-tree` skill during autonomous backlog maintenance
- Brainstorming new features for an area of the codebase
- Filling capacity gaps in the story hierarchy

## When NOT to Use

- Viewing or visualizing existing stories (use `story-tree` with "show story tree")
- Prioritizing which story to work on next (use `prioritize-story-notes`)
- Manually creating 1-2 specific stories (just add them directly to the database)
- Projects without git history (stories need evidence)

## Multi-Node Batching (CI Optimization)

When called with multiple node IDs (e.g., "Generate stories for nodes: 1.2, 1.3"):

1. **Parse all node IDs** from the instruction
2. **Perform Steps 0-2 once** (goals check, git analysis) - these are shared context
3. **Loop through nodes for Steps 3-6**: For each node, run context gathering, gap analysis, and story generation
4. **Output single combined report** (or minimal CI output) covering all nodes

**Token savings:** Processing N nodes in one invocation avoids loading this skill document N times, saving ~2,800 tokens per additional node.

**Distribution rule:** Generate max 1 story per node when batching, total max 2 stories across all nodes unless explicitly told otherwise.

## Storage

**Database:** `.claude/data/story-tree.db`
**Schema:** See `story-tree` skill references

## Environment Requirements

**CRITICAL:** Always use Python's sqlite3 module, NOT the sqlite3 CLI:

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('YOUR SQL HERE')
print(cursor.fetchall())
conn.close()
"
```

## Story Generation Workflow

### Step 0: Check for Product Goals Files (Optional but Recommended)

**BEFORE generating story ideas**, check if goals files exist to understand what the product IS and what it is NOT:

**Goals Files (if they exist):**
- `ai_docs/goals.md` - Product direction, target user, core capabilities, guiding principles
- `ai_docs/non-goals.md` - Explicit exclusions, anti-patterns, YAGNI items

**Check and load goals files in one step:**
```python
python -c "
import os, json
result = {'goals': None, 'non_goals': None, 'has_goals': False, 'has_non_goals': False}
for key, path in [('goals', 'ai_docs/goals.md'), ('non_goals', 'ai_docs/non-goals.md')]:
    if os.path.exists(path):
        result[f'has_{key}'] = True
        with open(path) as f:
            result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

**Using the result**, internalize:
1. **What the product IS**: Target user, core capabilities, guiding principles
2. **What the product is NOT**: Explicit exclusions, anti-patterns to avoid
3. **Philosophical boundaries**: What kinds of features align vs. conflict with product goals

**Why this matters:**
- Stories that align with goals = higher approval rate
- Stories that conflict with non-goals = instant rejection
- Understanding boundaries = better gap identification

**If goals files do NOT exist:**
- Skip goals-based filtering
- Generate stories based purely on git commits and gap analysis
- Consider suggesting the user run the `goal-synthesis` skill to create goals files

**Action:** Check for files, read them if they exist, then proceed to context gathering.

### Step 1: Gather Context for Parent Node

Query the parent node and its existing children:

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get parent node details
cursor.execute('''
    SELECT id, title, description, status, capacity,
           (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = :node_id AND depth = 1) as child_count,
           (SELECT MIN(depth) FROM story_paths WHERE descendant_id = :node_id) as node_depth
    FROM story_nodes
    WHERE id = :node_id
''', {'node_id': 'TARGET_NODE_ID'})

parent = dict(cursor.fetchone())
print('=== PARENT NODE ===')
print(json.dumps(parent, indent=2))

# Get existing children
cursor.execute('''
    SELECT s.id, s.title, s.description, s.status
    FROM story_nodes s
    JOIN story_paths sp ON s.id = sp.descendant_id
    WHERE sp.ancestor_id = :node_id AND sp.depth = 1
    ORDER BY s.created_at
''', {'node_id': 'TARGET_NODE_ID'})

children = [dict(row) for row in cursor.fetchall()]
print('\n=== EXISTING CHILDREN ===')
print(json.dumps(children, indent=2))

conn.close()
"
```

### Step 2: Analyze Relevant Git Commits

Look for commit patterns related to the parent node's scope:

```python
python -c "
import subprocess
import re

# Get recent commits (last 30 days or since last analysis)
result = subprocess.run([
    'git', 'log',
    '--since=30 days ago',
    '--pretty=format:%h|%ai|%s',
    '--no-merges'
], capture_output=True, text=True)

commits = []
for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split('|')
        commits.append({
            'hash': parts[0],
            'date': parts[1],
            'message': parts[2]
        })

# Filter commits relevant to parent node context
# Look for keywords from parent title/description
print('\n'.join([f\"{c['hash']} - {c['message']}\" for c in commits]))
"
```

Match commits to parent node scope using keyword similarity.

### Step 3: Identify Story Gaps

Analyze what's missing based on evidence:

**Gap Analysis Types:**
1. **Functional gaps**: Features mentioned in parent but not covered by children
2. **Pattern gaps**: Commit patterns showing work without corresponding stories
3. **User journey gaps**: Steps in user workflows not yet addressed
4. **Technical gaps**: Infrastructure or foundation work needed

**If goals files exist, apply Goals-Aware Filtering:**
- **Cross-check against goals.md**: Does this gap align with core capabilities and guiding principles?
- **Cross-check against non-goals.md**: Does this gap fall into explicit exclusions or anti-patterns?
- **Reject speculative features**: If gap isn't grounded in goals OR commits, don't create a story
- **Red Flags**: Features that conflict with principles stated in goals.md, or are explicitly excluded in non-goals.md
- **Green Flags**: Features that directly support capabilities listed in goals.md

**If goals files do NOT exist:**
- Focus purely on evidence from git commits and functional gaps
- Avoid speculative features not grounded in actual development patterns
- Ensure stories decompose parent scope without adding new scope

**Generate max 3 stories per invocation** to prevent overwhelming the backlog.

### Step 4: Generate User Stories

For each identified gap, create a properly formatted user story:

**Story Format Template:**

```markdown
### [ID]: [Title]

**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context**: [Git commits or existing patterns that inform this story]
```

**Story ID Format:** `[parent-id].[N]` where N is next available child number

**Story Quality Guidelines:**
- **Specific user role**: Not "user" - be precise based on who the product serves (derive from goals file if available, or from codebase context)
- **Concrete capability**: What exactly can they do? (e.g., "configure polling interval" not "change settings")
- **Measurable benefit**: Why does this matter? (e.g., "reduce manual time entry" not "improve experience")
- **Testable criteria**: Each criterion must be verifiable (e.g., "Settings persist after restart" not "Settings work correctly")

**Evidence-based requirements:**
- Each story must reference git commits OR existing gap in functionality
- Avoid speculative features not grounded in actual development patterns
- Stories should decompose parent scope, not add new scope

**Goals Alignment Requirements (if goals files exist):**
- **Aligns with product goals**: Story must support core capabilities listed in goals.md
- **Respects non-goals boundaries**: Story must NOT be an explicit exclusion listed in non-goals.md
- **Follows guiding principles**: Adhere to principles stated in goals.md
- **Target user focus**: Story should benefit the target user described in goals.md

### Step 5: Validate Stories

Before inserting, verify:

**Evidence & Format:**
- [ ] Each story has clear basis in commits or gap analysis
- [ ] Stories are specific and actionable
- [ ] Acceptance criteria are testable
- [ ] No duplicates with existing children
- [ ] User story format is complete (As a/I want/So that)
- [ ] IDs follow [parent-id].[N] format
- [ ] Story scope fits within parent's description

**Goals Alignment (if goals files exist):**
- [ ] Story aligns with at least one core capability from goals.md
- [ ] Story does NOT conflict with any explicit exclusion in non-goals.md
- [ ] Story follows guiding principles stated in goals.md
- [ ] Story benefits target user described in goals.md
- [ ] Story does NOT introduce anti-patterns listed in non-goals.md
- [ ] Story does NOT implement YAGNI items unless explicitly requested

**Non-Goals Red Flag Check (if non-goals.md exists):**
Ask yourself: "Would this story be rejected based on the non-goals file?"
- Review the explicit exclusions in non-goals.md
- Check if the story matches any anti-patterns listed
- If any red flag triggers, do NOT create the story

**If goals files do NOT exist:**
- Focus validation on evidence quality and format requirements
- Ensure stories are grounded in git commits or clear functional gaps

### Step 6: Insert Stories into Database

**Default status:** New stories start as `concept` (requires human approval)

**Exception:** When user explicitly says "generate stories for [node-id]", create with `status: 'approved'` instead.

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Insert story (capacity NULL = dynamic)
cursor.execute('''
    INSERT INTO story_nodes (id, title, description, status, created_at, updated_at)
    VALUES (?, ?, ?, 'concept', datetime('now'), datetime('now'))
''', ('NEW_ID', 'STORY_TITLE', 'FULL_STORY_DESCRIPTION'))

# Populate closure table
cursor.execute('''
    INSERT INTO story_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, ?, depth + 1
    FROM story_paths WHERE descendant_id = ?
    UNION ALL SELECT ?, ?, 0
''', ('NEW_ID', 'PARENT_ID', 'NEW_ID', 'NEW_ID'))

conn.commit()
conn.close()
print('Story inserted successfully')
"
```

Repeat for each generated story (max 3).

### Step 7: Output Generation Report

```markdown
# Story Brainstorming Report

**Generated:** [ISO timestamp]
**Parent Node:** [ID] - "[Title]"

## Goals Status

**Goals files found:** [Yes/No]
- `ai_docs/goals.md`: [Exists/Not found]
- `ai_docs/non-goals.md`: [Exists/Not found]

[If goals files exist, include:]
## Goals Alignment Summary

**Product Goals Review:** ✓ Completed
- Core capabilities considered: [list relevant capabilities from goals.md]
- Anti-patterns avoided: [list any non-goals items that were filtered out]
- Guiding principles applied: [list relevant principles]

[If goals files do NOT exist, include:]
## Note on Goals Files

Goals files not found. Stories generated based on git commits and gap analysis only.
Consider running the `goal-synthesis` skill to create goals files for better story alignment.

## Context Analysis

**Existing Children:** [N] stories
**Capacity:** [current]/[effective_capacity]
**Node Depth:** Level [N]

## Git Commits Analyzed

[List of relevant commits that informed story generation]

## Gaps Identified

1. [Gap description and why it needs a story]
   [If goals files exist:] - **Goals alignment**: [How this gap supports product goals]
2. [Gap description and why it needs a story]
   [If goals files exist:] - **Goals alignment**: [How this gap supports product goals]
3. [Gap description and why it needs a story]
   [If goals files exist:] - **Goals alignment**: [How this gap supports product goals]

## Gaps Rejected

[If goals files exist:]
[List any gaps that were identified but rejected due to non-goals conflicts]
- [Gap description] - **Reason**: Conflicts with [specific non-goals item]

[If goals files do NOT exist:]
[List any gaps rejected due to lack of evidence or scope creep]

## Generated Stories

### Story 1: [ID] - [Title]

**As a** [role]
**I want** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Related context**: [Git commits or gaps]

**Status:** concept (pending approval)

---

[Repeat for Story 2 and Story 3 if generated]

## Next Steps

- Review generated stories and approve/reject/refine as needed
- Use `story-tree` to update status: "Mark [story-id] as approved"
- Generated stories will appear in next tree visualization
```

### Step 7 (CI Mode): Minimal Output

**When running in CI/automation context** (e.g., scheduled GitHub Actions), use this minimal output format instead of the full report:

**Single node:**
```
✓ Generated [N] stories for node [PARENT_ID]:
  - [STORY_ID_1]: [Title 1]
  - [STORY_ID_2]: [Title 2]
```

**Multi-node batch:**
```
✓ Generated [N] stories across [M] nodes:
  [NODE_1]: [STORY_ID_1] - [Title 1]
  [NODE_2]: [STORY_ID_2] - [Title 2]
```

**CI mode indicators:**
- Running via GitHub Actions workflow
- Called by `/write-stories` command in autonomous mode
- No interactive user session

**Benefits:** Reduces token usage by ~500 tokens per invocation while preserving essential feedback.

## Integration with Story-Tree

This skill is designed to work standalone OR be invoked by `story-tree`:

**Standalone usage:**
```
User: "Brainstorm stories for node 1.2"
→ Runs full workflow for that specific node
```

**Invoked by story-tree:**
```
story-tree identifies under-capacity node → calls brainstorm-story → inserts results
```

## Story Status Lifecycle

Stories created by this skill start at `concept`:

```
concept → approved → planned → active → implemented → released
          ↓
       rejected/wishlist
```

Human approval required to move from `concept` to `approved`.

## Quality Checks Checklist

Before finalizing any story generation:

**Evidence & Format:**
- [ ] Each story has clear evidence (commits or gaps)
- [ ] User story format is complete (As a/I want/So that)
- [ ] Acceptance criteria are specific and testable (3+ criteria)
- [ ] Related context section explains the evidence
- [ ] Story title is concise and descriptive
- [ ] Story description stays within parent scope
- [ ] No duplicate functionality with existing children
- [ ] IDs follow proper hierarchy format
- [ ] Maximum 3 stories generated per invocation

**Goals Alignment (if goals files exist):**
- [ ] Checked for ai_docs/goals.md and ai_docs/non-goals.md
- [ ] Reviewed goals files before generating stories (if they exist)
- [ ] Each story aligns with core capabilities from goals.md
- [ ] No story conflicts with explicit exclusions from non-goals.md
- [ ] No story introduces anti-patterns listed in non-goals.md
- [ ] No story implements YAGNI items without explicit request
- [ ] Stories follow guiding principles from goals.md
- [ ] Stories benefit target user described in goals.md

**If goals files do NOT exist:**
- [ ] Stories are grounded in git commits or clear functional gaps
- [ ] No speculative features without evidence
- [ ] Consider recommending the `goal-synthesis` skill to the user

## Common Mistakes (STOP Before Making These)

| Mistake | Why It Happens | What To Do Instead |
|---------|----------------|-------------------|
| Using `sqlite3` CLI command | Copy-pasting shell-looking examples | Use Python's sqlite3 module (see Environment Requirements) |
| Generating >3 stories | Trying to be thorough | Limit to 3 - story-tree will call again if needed |
| Speculative features | Not grounding in evidence | Every story must reference commits OR specific gap |
| Generic user roles | "As a user" is too vague | Be specific based on target user from goals file or codebase context |
| Vague acceptance criteria | "Feature works correctly" | Make testable: "Setting persists after restart" |
| Adding new scope | Expanding beyond parent | Stories decompose parent, don't expand it |
| **Skipping goals check** | Rushing to generate stories | **ALWAYS check for goals files FIRST (Step 0)** |
| **Ignoring non-goals** | Assuming features are wanted | If non-goals exists, check exclusions before creating stories |
| **Features without evidence** | Building what seems helpful | Ground every story in git commits or functional gaps |
| **Complex configuration** | Over-engineering settings | Avoid YAGNI items unless explicitly requested |
| **Generic features** | Forgetting target user | Focus on target user described in goals file or inferred from codebase |

## Examples

### Good Story Example (with goals files)

```markdown
### 1.2.3: Add keyboard shortcut for quick task creation

**As a** project manager
**I want** to create new tasks with a keyboard shortcut from any screen
**So that** I can capture tasks quickly without interrupting my workflow

**Acceptance Criteria:**
- [ ] Ctrl+N opens quick task creation modal from any screen
- [ ] Modal pre-fills project based on current context
- [ ] Task is saved and appears in task list immediately
- [ ] Shortcut is configurable in settings

**Related context**: Commits abc123, def456 added task creation flow, but gap analysis shows no keyboard-driven path exists. Aligns with "quick capture" and "minimize workflow interruption" principles from goals.md.

**Goals alignment**:
- Core capability: Quick task capture (from goals.md)
- Guiding principle: Minimize workflow interruption
- Target user: Project managers (from goals.md)
```

### Good Story Example (without goals files)

```markdown
### 1.2.3: Add keyboard shortcut for quick task creation

**As a** [role inferred from codebase: project manager based on existing UI copy]
**I want** to create new tasks with a keyboard shortcut from any screen
**So that** I can capture tasks quickly without interrupting my workflow

**Acceptance Criteria:**
- [ ] Ctrl+N opens quick task creation modal from any screen
- [ ] Modal pre-fills project based on current context
- [ ] Task is saved and appears in task list immediately
- [ ] Shortcut is configurable in settings

**Related context**: Commits abc123, def456 added task creation flow. Gap analysis shows no keyboard-driven path exists, which is common in task management apps for power users.

**Note**: No goals files found. Consider running `goal-synthesis` skill to create them.
```

### Bad Story Example (Non-Goals Violation - if non-goals exists)

```markdown
### 1.2.3: Add analytics dashboard

**As a** user
**I want** to view charts and graphs showing my usage over time
**So that** I can see patterns in my behavior

**Acceptance Criteria:**
- [ ] Dashboard shows pie charts of usage
- [ ] Weekly/monthly view toggles
- [ ] Export charts as PNG

**Related context**: Users might want to see analytics
```

**Problems:**
- **CRITICAL: Check non-goals** - If analytics dashboards are excluded in non-goals.md, this story should not be created
- Generic role ("user" instead of specific target user)
- Not grounded in evidence ("might want" is speculation)
- Check if this conflicts with guiding principles in goals.md

### Bad Story Example (Format Issues)

```markdown
### 1.2.4: Improve settings

**As a** user
**I want** better settings
**So that** the app works better

**Acceptance Criteria:**
- [ ] Settings are good
- [ ] App is improved

**Related context**: We should have better settings
```

**Problems:**
- Vague title ("Improve settings")
- Generic role ("user") - use target user from goals file or infer from codebase
- Non-specific capability ("better settings")
- Unmeasurable benefit ("works better")
- Untestable criteria ("settings are good")
- No evidence (no commits or gaps cited)

## References

**Goals Files (check for existence first):**
- **Product Goals:** `ai_docs/goals.md` - What the product IS (target user, core capabilities, guiding principles)
- **Non-Goals:** `ai_docs/non-goals.md` - What the product is NOT (explicit exclusions, anti-patterns, YAGNI items)
- **Note:** These files may not exist in all projects. Check for existence before attempting to read.

**Story Tree System:**
- **Story Tree Database:** `.claude/data/story-tree.db`
- **Story Tree Skill:** `.claude/skills/story-tree/SKILL.md`
- **Schema:** `.claude/skills/story-tree/references/schema.sql`
- **21-Status System:** See story-tree skill SKILL.md for full status definitions
- **Goal Synthesis Skill:** `.claude/skills/goal-synthesis/SKILL.md` - Use to generate goals files if they don't exist
