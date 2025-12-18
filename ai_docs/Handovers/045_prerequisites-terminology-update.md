# Handover: Prerequisites Terminology Update

## Task

Distinguish between **dependencies** (external libraries/systems) and **prerequisites** (stories that must complete before another story can activate).

### Three Changes Required

1. **Terminology update across codebase** - Replace "dependency/dependencies" with "prerequisites" where referring to story-to-story relationships
2. **Update story-writing skill** - Add explicit prerequisites identification to story template
3. **Update activate-stories.yml** - Refocus on triaging planned stories by checking prerequisites

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/story-writing/SKILL.md` | Add prerequisites field to story template (Step 4) |
| `.github/workflows/activate-stories.yml` | Currently parses fuzzy text for deps; update to use structured prerequisites |
| `.claude/skills/story-execution/SKILL.md` | Has dependency check in Step 1.5; update terminology |
| `.claude/skills/story-tree/references/orchestrator-workflow-complete.md` | Spec doc; update terminology for consistency |

## Current State

### activate-stories.yml (lines 148-155)
Currently uses regex to parse dependencies from description/notes:
```python
dep_pattern = r'(?:depends on|requires|after|needs)\s+(\d+(?:\.\d+)*)|...'
```

This should check a structured `Prerequisites:` field instead.

### story-writing SKILL.md template (lines 107-121)
Current template has no prerequisites field:
```markdown
### [ID]: [Title]
**As a** [role]
**I want** [capability]
**So that** [benefit]
**Acceptance Criteria:** ...
**Related context**: [Git commits or gaps]
```

Add after Acceptance Criteria:
```markdown
**Prerequisites:** [story IDs or "None"]
```

## Proposed Prerequisites Instruction

Add to story-writing skill Step 4:

```markdown
**Prerequisites (for activation ordering):**
- Which sibling/cousin stories must be IMPLEMENTED before this one can be ACTIVATED?
- Examples: shared infrastructure, foundational features, data models
- Document as: `Prerequisites: 1.2.1, 1.3.4` or `Prerequisites: None`
- Only list story IDs from this tree, not external systems or libraries
```

## Context from Discussion

- **activate-stories purpose**: Sequencing which planned stories to activate first, NOT detecting problems
- **Prerequisites vs Dependencies**: "Dependencies" implies external libraries; "Prerequisites" better conveys story ordering
- The `blocked:ID1,ID2` format in hold_reason is correct - stores which stories are blocking activation
- Outcome A in execute-stories (blocking issues in plan) is separate concern - about plan quality, not sequencing

## Files to NOT Modify

- `execute-stories.yml` - Outcome A logic is correct and separate from prerequisites
- WIP files in `ai_docs/WIP/` - These document verification status, not implementation

## Branch

Continue on: `claude/orchestrator-workflow-transition-OKLXK`

## Verification After Changes

```bash
# Check terminology consistency
grep -r "depends on\|dependency" .claude/skills/ --include="*.md"
grep -r "Prerequisites:" .claude/skills/ --include="*.md"

# Verify activate-stories parses Prerequisites field
# Test with a planned story that has Prerequisites: set
```
