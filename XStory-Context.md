# XStory Development Tool - Context for Research

## Overview

**XStory** is an autonomous hierarchical story backlog management system that integrates with git to maintain and evolve a tree of user stories. It analyzes commit history to track implementation and automatically generates new stories based on capacity rules and gap analysis.

## Core Architecture

### Database: SQLite with Closure Table Pattern
- **Location**: `.claude/data/story-tree.db`
- **Pattern**: Closure table for efficient tree traversal
- **Tables**:
  - `story_nodes` - Story definitions, status tracking, metadata
  - `story_paths` - Ancestor-descendant relationships (depth tracking)
  - `story_commits` - Links git commits to implemented stories
  - `vetting_decisions` - Conflict resolution cache
  - `metadata` - System state (lastUpdated, lastAnalyzedCommit)

### Three-Dimensional Status Model (v4.0)

Stories are tracked using three orthogonal fields instead of a single status:

**1. Stage** (workflow position):
- `concept` → `approved` → `planned` → `active` → `reviewing` → `verifying` → `implemented` → `ready` → `polish` → `released`

**2. Hold Reason** (temporary blocks):
- `queued`, `pending`, `paused`, `blocked`, `broken`, `polish`, `conflict`, `wishlist`
- When set, stage is preserved for resumption

**3. Disposition** (terminal states):
- `rejected`, `infeasible`, `duplicative`, `legacy`, `deprecated`, `archived`
- Mutually exclusive with hold_reason
- Preserves stage for historical context

**Human Review Flag**: `human_review = 1` when story needs attention

## Capacity-Based Growth Algorithm

**Dynamic Capacity**: `effective_capacity = capacity_override OR (3 + count(implemented/ready children))`

**Priority**: Breadth-first (shallower nodes first)

**Exclusions from generation**:
- `stage = 'concept'` (not yet approved)
- `hold_reason IS NOT NULL` (needs resolution)
- `disposition IS NOT NULL` (terminal state)

**Algorithm**:
1. Find all under-capacity nodes
2. Order by depth (ascending) to prioritize shallower levels
3. Generate stories for highest-priority target
4. Encourages finishing work before expanding tree

## Git Integration

**Commit Analysis**:
- Incremental from `lastAnalyzedCommit` checkpoint
- Extracts keywords from commit messages
- Similarity scoring against story descriptions
- Auto-updates story stage to `implemented` on strong matches
- Stores relationships in `story_commits` table

**Staleness Protection**:
- Auto-updates if `lastUpdated` > 3 days old
- Ensures tree stays synchronized with development

## Skill Ecosystem

**Core Skills**:
- `story-tree` - Autonomous orchestrator, tree visualization
- `story-building` - Generate evidence-based stories with vetting
- `story-vetting` - Detect duplicates, overlaps, conflicts
- `story-planning` - Create TDD implementation plans
- `story-execution` - Execute plans with RED-GREEN-COMMIT cycles
- `story-verification` - Validate acceptance criteria
- `prioritize-story-notes` - Identify next work items
- `goal-synthesis` - Export goals/non-goals documentation

**Shared Utilities**: `.claude/skills/story-tree/utility/story_db_common.py`
- Database operations (get_connection, delete_story, reject_concept, etc.)
- Status computation (compute_effective_status)
- Merge operations (merge_concepts)
- DRY principle across all skills

## Workflow Examples

### Autonomous Operation
```
User: "update story tree"
→ Analyze git commits since last checkpoint
→ Identify highest-priority under-capacity node
→ Invoke story-building for that node
→ Output report with tree visualization
```

### Conflict Detection
```
User: "vet stories"
→ Compare all concept stories pairwise
→ Classify: duplicate/scope_overlap/competing/incompatible
→ Cache decisions in vetting_decisions table
→ Present conflicts for human review
```

### Implementation Cycle
```
1. User approves concept → stage='approved'
2. story-planning creates TDD plan → stage='planned'
3. prioritize-story-notes identifies best candidate
4. story-execution runs plan → stage='active' → 'reviewing' → 'verifying'
5. story-verification validates criteria → stage='implemented'
6. Git commit analysis confirms → links in story_commits
```

## Key Design Principles

**Breadth over Depth**: Prioritize shallower nodes to maintain strategic balance

**Evidence-Based**: Stories generated from commit analysis and gap identification, not speculation

**Minimal Human Intervention**: Autonomous by default, requests clarification only for ambiguity

**DRY Database Operations**: All skills use shared utility module for consistency

**Incremental Analysis**: Only process new commits since last checkpoint for efficiency

**Quality Gates**: Stories must have clear basis, testable criteria, no duplicates

## File Structure

```
.claude/
├── data/
│   ├── story-tree.db              # SQLite database
│   └── plans/                     # Implementation plans
├── skills/
│   ├── story-tree/
│   │   ├── SKILL.md               # Main orchestrator
│   │   ├── references/            # Schema, queries, rationales
│   │   ├── scripts/tree-view.py   # Visualization
│   │   └── utility/story_db_common.py  # Shared operations
│   ├── story-building/
│   ├── story-vetting/
│   ├── story-planning/
│   ├── story-execution/
│   ├── story-verification/
│   ├── prioritize-story-notes/
│   └── goal-synthesis/
└── commands/
    ├── plan-story.md
    └── write-story.md
```

## Environment Constraints

- **No sqlite3 CLI**: Always use Python's sqlite3 module
- **Script Paths**: Use `.claude/skills/story-tree/scripts/` NOT project root `scripts/`
- **Database Path**: Always `.claude/data/story-tree.db`

## Common Queries

**Find under-capacity nodes**:
```python
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('''
SELECT s.id, s.title,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as children,
    COALESCE(s.capacity, 3 + (
        SELECT COUNT(*) FROM story_paths sp
        JOIN story_nodes child ON sp.descendant_id = child.id
        WHERE sp.ancestor_id = s.id AND sp.depth = 1
        AND child.stage IN ('implemented', 'ready', 'released')
        AND child.disposition IS NULL
    )) as effective_capacity
FROM story_nodes s
WHERE s.stage != 'concept'
  AND s.hold_reason IS NULL
  AND s.disposition IS NULL
HAVING children < effective_capacity
ORDER BY (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id)
''')
print(cursor.fetchall())
conn.close()
```

## Triggering XStory

**Phrases**:
- "update story tree" - Full autonomous workflow
- "generate stories" / "brainstorm stories" - Create new concepts
- "vet stories" - Detect conflicts
- "plan story" - Create implementation plan
- "execute plan" - Implement with TDD
- "verify story" - Check acceptance criteria
- "show story tree" / "tree status" - Visualization
- "synthesize goals" - Export documentation

## Use Cases

**Appropriate**:
- Hierarchical feature planning
- Evidence-based backlog generation
- Git-driven implementation tracking
- Strategic portfolio balance
- Long-term product development

**Inappropriate**:
- Manual story entry (one-off items)
- Sprint/task management (operational, not strategic)
- Non-hierarchical backlogs
- Projects without git history
- Non-software projects

## Quality Standards

**Generated stories must have**:
- Clear basis in commit history or gap analysis
- Complete user story format (role, capability, benefit)
- Specific, actionable descriptions
- Testable acceptance criteria
- No duplicates of existing stories
- Alignment with established patterns

## Version History

- **v1.0**: Single status field
- **v2.0**: Status expansion (concept → implemented)
- **v3.0**: Capacity-based generation
- **v4.0**: Three-field model (stage + hold_reason + disposition)
