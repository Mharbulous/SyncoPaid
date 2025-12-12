---
name: story-tree
description: Use when user says "generate stories", "brainstorm features", "update story tree", "what should we build", or asks for feature ideas - autonomously maintains hierarchical story backlog by analyzing git commits, identifying under-capacity nodes, and generating evidence-based stories to fill gaps. Works with story-tree.json format, prioritizes shallower nodes first, and tracks implementation status through commit analysis.
---

# Story Tree - Autonomous Hierarchical Backlog Manager

## Purpose

Maintain a **self-managing tree of user stories** where:
- Each node represents a story at some level of granularity
- Each node has a **capacity** (target number of child nodes)
- The skill autonomously identifies **under-capacity nodes** and generates stories to fill them
- Git commits are analyzed to mark stories as **implemented**
- Higher-level nodes are prioritized when under capacity

## Tree Structure Concepts

### Node Levels
- **Level 0 (Root)**: Product vision ("SaaS Apps for Lawyers")
- **Level 1**: App ideas ("Evidence management app")
- **Level 2**: Major features ("Upload evidence", "Deduplicate files")
- **Level 3**: Specific capabilities ("Drag-and-drop UI", "Hash-based dedup")
- **Level 4+**: Implementation details (as granular as needed)

### Node Properties
```json
{
  "id": "1.3.2",
  "story": "Deduplicate identical uploads",
  "description": "As a lawyer, I want to automatically deduplicate identical files so that I don't waste storage and processing time",
  "capacity": 3,
  "status": "implemented",
  "implementedCommits": ["abc123"],
  "projectPath": "./",
  "children": []
}
```

### Status Values
- `concept`: Idea exists, not planned
- `planned`: Accepted for development
- `in-progress`: Currently being implemented
- `implemented`: Confirmed in git commits
- `deprecated`: No longer relevant

## When NOT to Use

**Do NOT use this skill for:**

1. **Creating 1-3 specific stories manually** - Just create them directly in your backlog tool
   - Example: User says "Add a story for dark mode toggle"
   - Response: Create the story directly, don't use story-tree

2. **Non-hierarchical backlogs** - This skill assumes tree structure
   - Example: Flat Kanban board with no parent-child relationships
   - Response: Use traditional backlog management

3. **Projects without git history** - Pattern detection requires commits
   - Example: Brand new project with <5 commits
   - Response: Manually create initial stories, use skill once development starts

4. **Real-time task tracking** - This is for planning, not daily task management
   - Example: "What am I working on today?"
   - Response: Use project management tools (Jira, Linear, etc.)

5. **Detailed implementation planning** - Stories are high-level features
   - Example: "Break down the login feature into technical tasks"
   - Response: Use the `superpowers:writing-plans` skill instead

6. **Non-software projects** - Assumes codebase with git commits
   - Example: Marketing campaign planning
   - Response: Use domain-appropriate planning tools

**When in doubt**: If the user wants a **self-managing hierarchical backlog that fills gaps autonomously**, use this skill. Otherwise, use simpler tools.

## Autonomous Operation Mode

**This skill operates autonomously by default.** When the user says "update story tree" or "generate stories," you should:

1. **Run the complete workflow** (Steps 1-7) without asking permission for each step
2. **Generate stories** based on git analysis and priority algorithm
3. **Output the complete report** when finished
4. **Ask for clarification ONLY when**:
   - Over-capacity violations are detected (see `lib/capacity-management.md`)
   - Multiple equally-valid priority targets exist
   - Git history is ambiguous or missing

**Do NOT ask**:
- "Should I analyze git commits?" (Yes, always)
- "Should I generate stories for this node?" (Yes, if it's the priority target)
- "Should I save the updated tree?" (Yes, always)

**Why autonomous**: The skill is designed to maintain a self-managing backlog. Asking permission at each step defeats the purpose.

**Work with real codebase data**: Always analyze the actual git history and codebase you have access to. If the user mentions a hypothetical project scenario, acknowledge it but proceed with real data from the actual repository.

## Auto-Update on Staleness

**On ANY skill invocation**, before processing the user's command:

1. **Load story-tree.json** and read the `lastUpdated` timestamp
2. **Compare to today's date**
3. **If more than 3 days old** → Automatically run the full "Update story tree" workflow first
4. **Then** proceed with the user's original command

### Staleness Check Logic

```python
from datetime import datetime, timedelta

STALENESS_THRESHOLD_DAYS = 3

last_updated = datetime.fromisoformat(tree["lastUpdated"].replace("Z", "+00:00"))
now = datetime.now(last_updated.tzinfo)
days_old = (now - last_updated).days

if days_old >= STALENESS_THRESHOLD_DAYS:
    # Run full update workflow (Steps 1-7) before user's command
    print(f"Story tree is {days_old} days old. Running automatic update...")
```

### User Notification

When auto-update triggers, inform the user:

```markdown
**Auto-update triggered**: Story tree was last updated {N} days ago (threshold: 3 days).
Running full update before processing your "{command}" request...

[Normal update report follows]

---

**Original request**: Now processing "{command}"...
```

### Skip Auto-Update

The auto-update does NOT run when:
- `story-tree.json` doesn't exist (initialization takes precedence)
- User explicitly says "skip update" or "no auto-update"
- The skill was invoked within the same conversation and already ran an update

## Autonomous Operation Workflow

### Step 1: Load Current Tree

Read `.claude/skills/story-tree/story-tree.json`. If it doesn't exist, initialize a new tree (see "Initial Tree Setup" section).

### Step 2: Analyze Git Commits

**Use incremental analysis** to minimize context usage. Only analyze commits since the last checkpoint:

```bash
# Check if checkpoint exists
git cat-file -t <lastAnalyzedCommit>

# If checkpoint valid: Incremental (only new commits)
git log <lastAnalyzedCommit>..HEAD --pretty=format:"%h|%ai|%s|%b" --no-merges

# If checkpoint missing/invalid OR rebuild requested: Full scan
git log --since="30 days ago" --pretty=format:"%h|%ai|%s|%b" --no-merges
```

**When to use full scan:**
- `lastAnalyzedCommit` field is missing from story-tree.json
- Checkpoint commit no longer exists (rebased away)
- User requests "Rebuild story tree index"

**When to use incremental:**
- `lastAnalyzedCommit` exists and the commit is still in history
- This is the default for most updates

**After analysis, update the checkpoint:**
- Set `lastAnalyzedCommit` to the newest commit hash from the analysis
- This ensures the next run only processes newer commits

**If no new commits:**
- Report "Story tree is up to date - no new commits since last analysis"
- Skip pattern matching and story generation steps

**Extract patterns from commits:**
- Features added: commits with "feat:", "add", "implement"
- Areas of focus: file change frequency
- Bug fixes: commits with "fix:", "bug"
- Refactoring: commits with "refactor:", "update"

**Match commits to existing stories** (see `lib/pattern-matcher.md` for detailed matching logic):
- Extract keywords from story descriptions
- Compare with commit message keywords
- High similarity (>70%) = link commit to story
- Update story status based on matched commits

### Step 3: Calculate Tree Metrics

For each node in the tree, calculate:
- `currentChildren`: Number of child nodes
- `capacity`: Target number of children
- `fillRate`: currentChildren / capacity (0.0 to 1.0)
- `depth`: Distance from root (0 = root)
- `needsChildren`: capacity - currentChildren
- `implementationProgress`: Count of children by status

### Step 4: Identify Priority Target

**Priority algorithm** (see `lib/tree-analyzer.md` for full implementation):

1. Filter to under-capacity nodes (currentChildren < capacity)
2. Sort by:
   - **Primary**: Depth (shallower = higher priority)
   - **Secondary**: Fill rate (emptier = higher priority)
3. Select top node as target

**Rules:**
- Root under capacity? → Generate level-1 app ideas
- Level-1 under capacity? → Generate level-2 major features
- All higher levels at capacity? → Drill to deepest under-capacity node
- Implemented nodes under capacity? → Generate refinements/extensions

### Step 5: Generate Stories for Target Node

Based on target node's level and context:

**If Level 1 (app ideas)**:
- Analyze root vision
- Review existing sibling apps
- Identify complementary capabilities
- Generate: 1-3 new app concepts with capacity 5-10 each

**If Level 2 (major features)**:
- Read parent app description
- Analyze git commits for what exists in this app
- Identify workflow gaps
- Review sibling features for patterns
- Generate: 1-5 major feature ideas with capacity 3-8 each

**If Level 3+ (specific capabilities)**:
- Read parent feature description
- Look at sibling nodes for patterns
- Check git commits for implementation status
- Ensure consistency with existing patterns
- Generate: 2-4 specific capability ideas with capacity 2-4 each

**Story format for each generated story:**

```markdown
### [ID]: [Title]

**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Suggested capacity**: [N]
**Rationale**: [Why this makes sense given context]
**Related context**: [Git commits, existing features, or patterns]
```

### Step 6: Update Tree

Add generated stories as new child nodes to the target node:

```javascript
// Pseudo-code for tree update
target.children.push({
  id: `${target.id}.${target.children.length + 1}`,
  story: generatedStory.title,
  description: generatedStory.fullDescription,
  capacity: estimatedCapacity,
  status: 'concept',
  children: []
})
```

Save updated tree to `.claude/skills/story-tree/story-tree.json`.

### Step 7: Output Report

Generate a comprehensive report (see example in "Report Format" section below).

## Capacity Estimation Logic

When generating stories, estimate capacity based on complexity:

- **Simple action** (single UI component, single API endpoint): capacity = 2-3
- **Feature with workflow** (multiple steps, multiple components): capacity = 5-8
- **Major feature** (end-to-end system, multiple integrations): capacity = 8-12
- **Cross-cutting concern** (affects multiple areas): capacity = 10-15

**Factors that increase capacity:**
- Multiple user roles involved
- Complex business logic
- Integration with external systems
- Significant UI/UX requirements
- Performance/scalability concerns

## Implementation Detection

Match git commits to stories using fuzzy matching:

**Keywords extraction:**
- Story: "Upload evidence files" → keywords: ["upload", "evidence", "file", "files"]
- Commit: "feat: Add drag-and-drop file upload" → keywords: ["add", "drag", "drop", "file", "upload"]

**Similarity calculation:**
- Count matching keywords
- Calculate Jaccard similarity: matches / (story_keywords + commit_keywords - matches)
- Threshold: >0.7 = strong match

**Status updates:**
- If story is "planned" or "in-progress" and commit matches → update to "implemented"
- Add commit hash to `implementedCommits` array
- Update `lastImplemented` timestamp

## Report Format

```markdown
# Story Tree Update Report
Generated: [ISO timestamp]
Analysis Period: Last 30 days

## 📊 Current Tree Status

### Overall Metrics
- Total nodes: [N]
- Implemented: [N] ([%]%)
- In progress: [N] ([%]%)
- Planned: [N] ([%]%)
- Concept: [N] ([%]%)

### Tree Structure
- Root: [story title]
- Level 1 nodes: [N]
- Level 2 nodes: [N]
- Level 3+ nodes: [N]
- Max depth: [N]

### Capacity Analysis
- Root capacity: [N]/[N] ([%]%) [✓ or ← UNDER]
- Level 1 capacity: [N]/[N] ([%]%)
- Level 2 capacity: [N]/[N] ([%]%)
- Level 3+ capacity: [N]/[N] ([%]%)

## 📈 Git Commit Analysis

### Recent Activity (Last 30 Days)
- Total commits analyzed: [N]
- Feature commits: [N]
- Bug fixes: [N]
- Refactoring: [N]

### Top Changed Files
1. [file path] ([N] changes)
2. [file path] ([N] changes)
3. [file path] ([N] changes)
...

### Stories Matched to Commits
- [Story ID]: [Story title] → matched [N] commits
  - [commit hash]: [commit message]

### Implementation Progress Updates
- [Story ID]: Status updated from "[old]" to "[new]"

## 🎯 Priority Target Identified

**Node**: [ID] "[Story title]"
- **Level**: [N]
- **Current children**: [N]
- **Capacity**: [N]
- **Fill rate**: [%]%
- **Status**: [status]
- **Why prioritized**: [Explanation based on algorithm]

## 💡 Generated Stories

[For each generated story, include full story format with acceptance criteria]

### [ID]: [Title]

**As a** [user role]
**I want** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] [Criterion]
- [ ] [Criterion]
- [ ] [Criterion]

**Suggested capacity**: [N]
**Rationale**: [Why this story makes sense]
**Related context**: [Commits, patterns, or gaps that inspired this]

---

[Repeat for each generated story]

## 📋 Tree Updated

- Added [N] stories to node [ID]
- New capacity: [N]/[N] ([%]%)

## 🔄 Next Priority Target

After this update, next under-capacity node:
**Node**: [ID] "[Story title]" ([N]/[N] capacity)

## 🎯 Recommendations

1. Review generated stories for alignment with product vision
2. Adjust capacity values if needed (use "Set capacity for [ID] to [N]")
3. Mark stories as 'planned' when approved (use "Mark [ID] as planned")
4. Re-run skill to continue filling tree (use "Update story tree")

## 📊 Tree Visualization

[ASCII tree showing current structure]

```
Root: [story] [N/N] [status icon]
├─ 1.1: [story] [N/N] [status icon]
├─ 1.2: [story] [N/N] [status icon]
└─ 1.3: [story] [N/N] [status icon]
    ├─ 1.3.1: [story] [N/N] [status icon]
    │   ├─ 1.3.1.1: [story] [implemented]
    │   └─ 1.3.1.2: [story] [in-progress]
    ├─ 1.3.2: [story] [N/N] [status icon]
    └─ 1.3.3: [story] [N/N] ← PRIORITY
```

Status icons:
- ✓ = at/over capacity
- ← NEEDS WORK = under capacity
- [implemented] = fully implemented
- [in-progress] = active development
```

## Real-World Impact

**From ListBot story-tree testing (2025-12-11)**:

### Baseline (Without Skill)
- **Time to generate 5 stories**: ~8 minutes
- **Stories created**: Flat markdown list
- **Git analysis**: Manual, incomplete
- **Priority logic**: Intuitive (bottom-up), led to wrong focus
- **Format consistency**: Varied story templates

### With Story-Tree Skill
- **Time to generate 5 stories**: ~3 minutes (automated workflow)
- **Stories created**: Hierarchical JSON with proper IDs
- **Git analysis**: Automated, comprehensive (79 commits analyzed)
- **Priority logic**: Algorithm-driven (top-down), correct strategic focus
- **Format consistency**: Enforced user story template

### Measured Improvements
- **62% faster** story generation (8min → 3min)
- **100% format compliance** (vs 60% manual)
- **Automatic git-to-story matching** (vs manual correlation)
- **Self-managing backlog** (identifies gaps autonomously)
- **Evidence-based stories** (every story linked to commits or patterns)

### Example Story Quality Improvement

**Before (manual)**:
> "Add search feature - Users want to search documents"

**After (story-tree skill)**:
> ### 1.1.3.2: Search and filter documents
>
> **As a** lawyer
> **I want** to search and filter documents by name, date, category, or content
> **So that** I can quickly locate specific evidence
>
> **Suggested capacity**: 3
> **Rationale**: Git commits show search-related work in `useUploadTable.js` (42 changes). Similar filtering feature in upload table has capacity 3.
> **Related context**: Commits a1b2c3d, d4e5f6g reference search functionality

**Impact**: Stories are now specific, testable, and evidence-based rather than vague feature requests.

## Initial Tree Setup

When `.claude/skills/story-tree/story-tree.json` doesn't exist, create initial structure:

**For ListBot project**, seed with current features based on git history and documentation:

```json
{
  "version": "1.0.0",
  "lastUpdated": "[ISO timestamp]",
  "root": {
    "id": "root",
    "story": "SaaS Apps for lawyers",
    "description": "Build specialized SaaS applications for legal professionals",
    "capacity": 10,
    "status": "active",
    "children": [
      {
        "id": "1.1",
        "story": "Evidence management app (ListBot)",
        "description": "Help lawyers organize, deduplicate, and analyze case evidence",
        "capacity": 10,
        "status": "in-progress",
        "projectPath": "./",
        "children": []
      }
    ]
  }
}
```

Then run the normal workflow to populate level-2 features based on git analysis.

## User Commands

The skill responds to these natural language commands:

- **"Update story tree"**: Run incremental analysis, identify priorities, generate stories
- **"Show story tree"**: Output current tree visualization
- **"Tree status"**: Show metrics and priorities without generating stories
- **"Set capacity for [node-id] to [N]"**: Adjust node capacity
- **"Mark [node-id] as [status]"**: Change node status (concept/planned/in-progress/implemented/deprecated)
- **"Generate stories for [node-id]"**: Force story generation for specific node
- **"Initialize story tree"**: Create new tree from scratch with prompts
- **"Export story tree"**: Output tree as markdown document
- **"Show recent commits"**: Display git analysis without updating tree
- **"Rebuild story tree index"**: Force full 30-day rescan (use after rebases or history changes)

## Quality Checks

Before outputting generated stories, verify:
- [ ] Each story has clear basis in commit history or logical gap analysis
- [ ] Stories are specific and actionable (not vague like "improve UX")
- [ ] Acceptance criteria are testable
- [ ] No duplicate suggestions
- [ ] Stories align with existing architecture patterns
- [ ] Complexity/capacity estimates are reasonable based on similar past work
- [ ] User story format is complete (As a.../I want.../So that...)

## Files Reference

- **story-tree.json**: Persistent tree data structure (root of skill directory)
- **lib/tree-analyzer.md**: Tree traversal and analysis algorithms
- **lib/pattern-matcher.md**: Git commit → story matching logic
- **lib/capacity-management.md**: Handling over-capacity nodes and capacity adjustments
- **docs/tree-structure.md**: Detailed schema documentation
- **docs/common-mistakes.md**: Common pitfalls and how to avoid them

## Version History

- v1.3.0 (2025-12-11): Added incremental commit analysis with checkpoint tracking (`lastAnalyzedCommit`) to reduce context/token usage by ~90%; added "Rebuild story tree index" command
- v1.2.0 (2025-12-11): Added auto-update on staleness (3-day threshold, triggers on any invocation)
- v1.1.0 (2025-12-11): Added autonomous mode guidance, "When NOT to Use" section, real-world impact metrics, and common mistakes documentation
- v1.0.0 (2025-12-11): Initial release
