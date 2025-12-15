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

### Step 0: Review Product Vision (CRITICAL - Do This First)

**BEFORE generating any story ideas**, review the vision files to understand what the product IS and what it is NOT:

**Vision Files:**
- `.claude/data/user-vision.md` - Product direction, target user, core capabilities, guiding principles
- `.claude/data/user-anti-vision.md` - Explicit exclusions, anti-patterns, YAGNI items

**Read and internalize:**
1. **What the product IS**: Target user, core capabilities, guiding principles
2. **What the product is NOT**: Explicit exclusions, anti-patterns to avoid
3. **Philosophical boundaries**: What kinds of features align vs. conflict with product vision

**Why this matters:**
- Stories that align with vision = higher approval rate
- Stories that conflict with anti-vision = instant rejection
- Understanding boundaries = better gap identification

**Action:** Read both files before proceeding to context gathering.

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

### Step 3: Identify Story Gaps (Vision-Aware)

Analyze what's missing while respecting product vision:

**Gap Analysis Types:**
1. **Functional gaps**: Features mentioned in parent but not covered by children
2. **Pattern gaps**: Commit patterns showing work without corresponding stories
3. **User journey gaps**: Steps in user workflows not yet addressed
4. **Technical gaps**: Infrastructure or foundation work needed

**Vision-Aware Filtering:**
- **Cross-check against user-vision.md**: Does this gap align with core capabilities and guiding principles?
- **Cross-check against user-anti-vision.md**: Does this gap fall into explicit exclusions or anti-patterns?
- **Reject speculative features**: If gap isn't grounded in vision OR commits, don't create a story

**Red Flags (Skip These Gaps):**
- Features that conflict with "un-intrusive background app" principle
- Analytics/reporting dashboards not tied to core time-tracking workflow
- Configuration complexity without clear value (YAGNI items)
- Features the user explicitly rejected or listed in anti-vision

**Green Flags (Prioritize These Gaps):**
- Improves AI-powered categorization accuracy
- Reduces manual effort for lawyers
- Better context capture (URLs, email subjects, folder paths)
- Non-intrusive prompting at natural work breaks
- Learning and improvement capabilities

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
- **Specific user role**: Not "user" - be precise (e.g., "lawyer", "developer", "end user")
- **Concrete capability**: What exactly can they do? (e.g., "configure polling interval" not "change settings")
- **Measurable benefit**: Why does this matter? (e.g., "reduce manual time entry" not "improve experience")
- **Testable criteria**: Each criterion must be verifiable (e.g., "Settings persist after restart" not "Settings work correctly")

**Evidence-based requirements:**
- Each story must reference git commits OR existing gap in functionality
- Avoid speculative features not grounded in actual development patterns
- Stories should decompose parent scope, not add new scope

**Vision Alignment Requirements:**
- **Aligns with product vision**: Story must support core capabilities (automatic capture, AI categorization, non-intrusive prompting, etc.)
- **Respects anti-vision boundaries**: Story must NOT be an explicit exclusion (analytics dashboards, screenshot galleries, intrusive UI, etc.)
- **Follows guiding principles**: "Minimize manual effort", "non-intrusive intelligence", "preserve all history", "learn and improve", "lawyer-specific workflows"
- **Target user focus**: Story should benefit lawyers tracking billable hours, not generic productivity users

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

**Vision Alignment (CRITICAL):**
- [ ] Story aligns with at least one core capability from user-vision.md
- [ ] Story does NOT conflict with any explicit exclusion in user-anti-vision.md
- [ ] Story follows guiding principles (minimize manual effort, non-intrusive, etc.)
- [ ] Story benefits target user (lawyers tracking billable hours)
- [ ] Story does NOT introduce anti-patterns (intrusive UI, feature bloat, rebuilding existing tools)
- [ ] Story does NOT implement YAGNI items unless explicitly requested

**Vision Red Flag Check:**
Ask yourself: "Would this story be rejected based on the anti-vision file?"
- Analytics/reporting dashboard? → REJECT
- Standalone screenshot gallery? → REJECT (unless AI-assisted clarification workflow)
- Global hotkeys or popup overlays? → REJECT
- Configuration complexity without clear value? → REJECT
- Rebuilding what lawyers already have elsewhere? → REJECT

If any red flag triggers, do NOT create the story.

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

## Vision Alignment Summary

**Product Vision Review:** ✓ Completed
- Core capabilities considered: [list relevant capabilities from user-vision.md]
- Anti-patterns avoided: [list any anti-vision items that were filtered out]
- Guiding principles applied: [list relevant principles]

## Context Analysis

**Existing Children:** [N] stories
**Capacity:** [current]/[effective_capacity]
**Node Depth:** Level [N]

## Git Commits Analyzed

[List of relevant commits that informed story generation]

## Gaps Identified

1. [Gap description and why it needs a story]
   - **Vision alignment**: [How this gap supports product vision]
2. [Gap description and why it needs a story]
   - **Vision alignment**: [How this gap supports product vision]
3. [Gap description and why it needs a story]
   - **Vision alignment**: [How this gap supports product vision]

## Gaps Rejected (Vision Conflicts)

[List any gaps that were identified but rejected due to anti-vision conflicts]
- [Gap description] - **Reason**: Conflicts with [specific anti-vision item]

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

**Vision Alignment (CRITICAL - DO NOT SKIP):**
- [ ] Reviewed user-vision.md before generating stories
- [ ] Reviewed user-anti-vision.md before generating stories
- [ ] Each story aligns with at least one core capability
- [ ] No story conflicts with explicit exclusions
- [ ] No story introduces anti-patterns (intrusive UI, feature bloat, etc.)
- [ ] No story implements YAGNI items without explicit request
- [ ] Stories follow guiding principles (minimize manual effort, non-intrusive, etc.)
- [ ] Stories benefit target user (lawyers tracking billable hours)

## Common Mistakes (STOP Before Making These)

| Mistake | Why It Happens | What To Do Instead |
|---------|----------------|-------------------|
| Using `sqlite3` CLI command | Copy-pasting shell-looking examples | Use Python's sqlite3 module (see Environment Requirements) |
| Generating >3 stories | Trying to be thorough | Limit to 3 - story-tree will call again if needed |
| Speculative features | Not grounding in evidence | Every story must reference commits OR specific gap |
| Generic user roles | "As a user" is too vague | Be specific: "lawyer", "developer", "end user" |
| Vague acceptance criteria | "Feature works correctly" | Make testable: "Setting persists after restart" |
| Adding new scope | Expanding beyond parent | Stories decompose parent, don't expand it |
| **Skipping vision review** | Rushing to generate stories | **ALWAYS read vision files FIRST (Step 0)** |
| **Analytics/dashboard stories** | Assuming users want reporting | Check anti-vision: explicitly excluded unless AI workflow |
| **Intrusive UI features** | Building what seems helpful | Check guiding principles: "non-intrusive intelligence" |
| **Screenshot gallery/viewer** | Assuming users need browsing | Check anti-vision: rejected unless AI-assisted clarification |
| **Complex configuration** | Over-engineering settings | Check anti-vision: avoid YAGNI items |
| **Generic productivity features** | Forgetting target user | Focus on lawyers tracking billable hours |

## Examples

### Good Story Example (Vision-Aligned)

```markdown
### 1.2.3: Detect email subject changes for automatic matter switching

**As a** lawyer using Outlook
**I want** the app to detect when I switch between emails with different subjects
**So that** the AI can automatically prompt me to categorize time spent on each matter

**Acceptance Criteria:**
- [ ] App captures email subject line when Outlook window is active
- [ ] Subject changes trigger new activity events in database
- [ ] Subject data is included in JSON export for AI categorization
- [ ] Works with both legacy Outlook and new Outlook (where supported)

**Related context**: Commits abc123, def456 added basic Outlook tracking, but gap analysis shows email subjects aren't captured for matter detection. Aligns with "context-aware categorization" and "capture rich contextual data" principles from user-vision.md.

**Vision alignment**:
- Core capability: Automatic activity capture, AI-powered categorization
- Guiding principle: Context-aware categorization (URLs, email subjects, folder paths)
- Target user: Lawyers tracking billable hours across multiple matters
```

### Bad Story Example (Don't Do This - Vision Violation)

```markdown
### 1.2.3: Add productivity analytics dashboard

**As a** user
**I want** to view charts and graphs showing my productivity over time
**So that** I can see how much time I spend in each application

**Acceptance Criteria:**
- [ ] Dashboard shows pie charts of app usage
- [ ] Weekly/monthly view toggles
- [ ] Export charts as PNG

**Related context**: Users might want to see productivity analytics
```

**Problems:**
- **CRITICAL: Violates anti-vision** - Analytics dashboards are explicitly excluded in user-anti-vision.md
- Generic role ("user" instead of "lawyer")
- Rebuilding existing tools (productivity analytics exist elsewhere)
- Not grounded in evidence ("might want" is speculation)
- Doesn't benefit target user's core need (billable time tracking, not productivity analytics)
- Violates guiding principle: "Use AI to save lawyers time, not rebuild what already exists elsewhere"

### Another Bad Example (Format Issues)

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
- Generic role ("user")
- Non-specific capability ("better settings")
- Unmeasurable benefit ("works better")
- Untestable criteria ("settings are good")
- No evidence (no commits or gaps cited)

## References

**Vision Files (READ FIRST):**
- **Product Vision:** `.claude/data/user-vision.md` - What the product IS (target user, core capabilities, guiding principles)
- **Anti-Vision:** `.claude/data/user-anti-vision.md` - What the product is NOT (explicit exclusions, anti-patterns, YAGNI items)

**Story Tree System:**
- **Story Tree Database:** `.claude/data/story-tree.db`
- **Story Tree Skill:** `.claude/skills/story-tree/SKILL.md`
- **Schema:** `.claude/skills/story-tree/references/schema.sql`
- **21-Status System:** See story-tree skill SKILL.md for full status definitions
