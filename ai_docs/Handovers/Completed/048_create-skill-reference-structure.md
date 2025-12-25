# 048: Create Skill Reference Structure

## Goal
Decompose `.claude/skills/story-execution/SKILL.md` (800 lines) into focused reference files that align with the multi-call workflow phases from handover 047.

## Context

Skills support progressive context disclosure via `references/` subfolder. The skill loader only includes reference files when explicitly requested, keeping base context small.

Current structure:
```
.claude/skills/story-execution/
└── SKILL.md  (800 lines - everything)
```

Target structure:
```
.claude/skills/story-execution/
├── SKILL.md  (orchestration only, ~50 lines)
├── temp-CI-notes.json  (shared state between calls)
└── references/
    ├── critical-review.md
    ├── tdd-execution.md
    ├── database-updates.md
    └── ci-mode-outcomes.md
```

## Mapping: Workflow Steps → Reference Files

From handover 047, Phase 5 steps map to references:

| Workflow Step | Reference File | Content from SKILL.md |
|---------------|----------------|----------------------|
| 5.1 Critical Review | `critical-review.md` | Step 2 (lines ~130-180) |
| 5.2+ Execute Batch | `tdd-execution.md` | Step 3-4 (lines ~180-250) |
| (all) DB updates | `database-updates.md` | SQL snippets (lines ~400-470) |
| (CI) Outcome handling | `ci-mode-outcomes.md` | CI Mode sections |

## Key Files

- `.claude/skills/story-execution/SKILL.md` - source to decompose
- `.claude/skills/story-tree/references/` - example of reference structure
- `.claude/skills/skill-refinement/references/` - another example

## Decomposition Strategy

1. **SKILL.md keeps**: Mode detection, announce message, orchestration logic ("if review passed, load tdd-execution.md")
2. **References get**: Detailed instructions, code snippets, output formats

## Orchestration Pattern

```markdown
# SKILL.md (simplified)

## Mode Detection
[CI vs Interactive - keep this]

## Workflow

### Review Phase
Load reference: `references/critical-review.md`
Write outcome to: `temp-CI-notes.json`

### Execution Phase
Load reference: `references/tdd-execution.md`
Read tasks from: `temp-CI-notes.json`

### Database Updates
Load reference: `references/database-updates.md`
```

## Tasks

1. Read current SKILL.md and identify section boundaries
2. Create `references/` directory
3. Extract sections into focused reference files
4. Rewrite SKILL.md as orchestration-only (~50 lines)
5. Test that skill still works interactively

## Output

Commit the new reference structure, then proceed to handover 049.

---

## Completion Status: ✅ COMPLETE

**Completed:** 2024-12-21
**Commit:** `b4e4c03 refactor: decompose story-execution skill into reference structure`

### Final Structure

```
.claude/skills/story-execution/
├── SKILL.md  (144 lines - orchestration)
└── references/
    ├── critical-review.md    (89 lines)
    ├── tdd-execution.md      (153 lines)
    ├── database-updates.md   (157 lines)
    └── ci-mode-outcomes.md   (158 lines)
```

### Verification
- SKILL.md now serves as orchestration, loading references as needed
- All reference files contain substantive content extracted from original
- temp-CI-notes.json created at runtime (not committed)
