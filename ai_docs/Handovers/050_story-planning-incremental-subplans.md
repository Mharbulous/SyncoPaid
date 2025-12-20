# 050: Update story-planning Skill to Generate Incremental Sub-Plans

## Task

Modify the story-planning skill to:
1. Assess plan complexity (low/medium/high)
2. For medium/high complexity, decompose into numbered incremental sub-plans
3. Order sub-plans for fail-fast bug discovery (errors surface immediately, not 3 steps later)

## Context

Currently, story-planning outputs a single monolithic plan. For complex features (like "Import Clients & Matters"), this creates risk: bugs introduced in step 1 may only manifest in step 4, making root cause identification difficult.

**Desired behavior**: Complex plans become sequences of small, independently verifiable sub-plans in `ai_docs/Handovers/` with sequential numbering (e.g., `045_`, `046_`, `047_`).

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/story-planning/SKILL.md` | **Primary file to modify** |
| `ai_docs/Handovers/045-049_*.md` | **Example of desired output pattern** |
| `.claude/skills/story-execution/SKILL.md` | Reference for how execution skill consumes plans |

## Current Workflow (Story-Planning Skill)

```
Query approved stories → Score/select → Research → Create single plan → Update stage
```

## Proposed Workflow

```
Query approved stories → Score/select → Research → Assess complexity →
  ├── LOW: Create single plan (current behavior)
  └── MEDIUM/HIGH: Decompose into numbered sub-plans → Create handover files
```

## Complexity Assessment Heuristics

Add after Step 4 (Research):

```markdown
### Step 4b: Assess Complexity

**Complexity indicators:**

| Indicator | Weight |
|-----------|--------|
| New database tables/migrations | +2 |
| New module file | +1 |
| UI changes | +1 |
| Multiple files modified | +1 per 3 files |
| External dependencies | +1 |
| Affects existing tests | +1 |

**Scoring:**
- 0-2 points: LOW → Single plan
- 3-5 points: MEDIUM → 2-4 sub-plans
- 6+ points: HIGH → 4+ sub-plans
```

## Sub-Plan Decomposition Rules

### Ordering Principle: Fail-Fast

Order sub-plans so each builds on verified foundation:

1. **Database/schema changes first** — Schema errors break everything downstream
2. **Core logic modules next** — Can be unit tested in isolation
3. **Integration points** — Connect modules, test wiring
4. **UI last** — Visual layer depends on all prior layers working

### Example: Import Clients & Matters

**Bad ordering** (bug in step 1 surfaces at step 4):
1. Menu integration
2. Dialog UI
3. Folder parser
4. Database schema ← Schema error here breaks steps 1-3

**Good ordering** (fail-fast):
1. Database schema ← Errors surface immediately
2. Folder parser ← Test in isolation
3. Dialog UI ← Depends on parser working
4. Menu integration ← Thin wiring, depends on dialog working

### Sub-Plan Template

Each sub-plan goes to `ai_docs/Handovers/NNN_[slug].md`:

```markdown
# NNN: [Feature] - [Sub-task]

## Task
[One sentence: what this sub-plan achieves]

## Context
[Why this comes before/after adjacent sub-plans]

## Scope
- [Bullet list of specific deliverables]

## Key Files

| File | Purpose |
|------|---------|
| `path/to/file.py` | [What to do with it] |

## Implementation
[Detailed steps, code snippets, verification commands]

## Verification
[Specific commands to prove this sub-plan works in isolation]

## Dependencies
- [Prior sub-plans that must be complete]

## Next Task
After this: `NNN+1_next-sub-plan.md`
```

## Integration with Existing Skill

### Changes to SKILL.md

**Add after Step 4 (Research Codebase):**

```markdown
### Step 4b: Assess Complexity & Decompose

**Assess complexity** using indicators above.

**If MEDIUM or HIGH:**
1. Identify logical boundaries (schema, logic, UI, integration)
2. Order for fail-fast (foundational → dependent)
3. Generate sub-plan files in `ai_docs/Handovers/`
4. Number sequentially from next available NNN
5. Each sub-plan is LOW complexity (2-5 tasks, 15-30 min)

**Sub-plan naming:** `NNN_[feature-slug]-[subtask-slug].md`
Example: `045_import-clients-matters-db-schema.md`
```

**Modify Step 5 (Create TDD Plan):**

For decomposed plans, Step 5 creates multiple files instead of one `.claude/data/plans/` file.

**Add orchestration file:**

When decomposing, also create:
`.claude/data/plans/YYYY-MM-DD-[story-id]-orchestration.md`

```markdown
# [Story Title] - Implementation Sequence

**Story ID:** [ID]
**Complexity:** [MEDIUM/HIGH]
**Sub-plans:** [N]

## Execution Order

1. `ai_docs/Handovers/045_db-schema.md` - Foundation
2. `ai_docs/Handovers/046_folder-parser.md` - Core logic
3. `ai_docs/Handovers/047_dialog-ui.md` - Integration
4. `ai_docs/Handovers/048_menu-integration.md` - Final wiring

## Rationale

[Why this ordering minimizes bug propagation]
```

### Changes to Output Format

**CI Mode - Decomposed plan:**
```
✓ Planned story [STORY_ID]: [Title]
  Complexity: MEDIUM
  Sub-plans: 4
  Files:
    - ai_docs/Handovers/045_db-schema.md
    - ai_docs/Handovers/046_folder-parser.md
    - ai_docs/Handovers/047_dialog-ui.md
    - ai_docs/Handovers/048_menu-integration.md
  Orchestration: .claude/data/plans/YYYY-MM-DD-orchestration.md
  Stage: approved -> planned
```

## Verification

After implementing changes:

1. Run skill on a known complex story
2. Verify it generates multiple handover files
3. Verify ordering follows fail-fast principle
4. Verify each sub-plan is independently verifiable

## Red Herrings (Ignore)

- `.claude/skills/story-execution/SKILL.md` — Don't modify; it already handles single plans correctly
- `.claude/skills/story-tree/` — Not relevant to planning decomposition
- `.claude/data/plans/*.md` — Existing single plans; don't migrate them

## Design Decisions Made

1. **Handover format over TDD format** — Sub-plans use handover style (context-rich, Sonnet-optimized) rather than strict TDD template
2. **ai_docs/Handovers/ location** — Consistent with existing handover conventions
3. **Orchestration file in .claude/data/plans/** — Links story-tree database to handover sequence
4. **Complexity threshold** — 3+ points triggers decomposition (tunable)

## Future Considerations

- story-execution skill may need updates to handle orchestration files
- Consider adding `sub_plans` field to story_nodes table for tracking
