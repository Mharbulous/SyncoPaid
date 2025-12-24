# Verify CI Command Extraction

Verify that the extracted CI slash commands preserve all logic from the original workflow.

---

## CONTEXT

The execute-stories.yml workflow (2292 lines) contained 5 embedded Claude prompts that have been
extracted and consolidated into 4 reusable slash commands. This verification ensures no logic was lost.

**Changes made:**
- `ci-validate-plan` renamed to `ci-identify-plan` (better reflects its purpose)
- `ci-verify-implementation` merged into `ci-review-plan` (eliminated redundancy)

## FILES TO COMPARE

### Original Workflow (Source of Truth)
`.claude/deprecated/execute-stories.yml`

### Extracted Commands (4 total)
| Command | Original Lines | Purpose |
|---------|----------------|---------|
| `.claude/commands/ci-identify-plan.md` | 386-482 | Match plan to story database |
| `.claude/commands/ci-review-plan.md` | 631-700 + 880-939 | Check implementation + critical review (merged) |
| `.claude/commands/ci-decompose-plan.md` | 1002-1135 | Assess complexity, split plans |
| `.claude/commands/ci-execute-plan.md` | 1378-1457 | Execute TDD steps |

## YOUR TASK

For EACH of the 4 commands:

1. **Read the original prompt(s)** from the deprecated workflow file
2. **Read the extracted command** file
3. **Compare systematically:**
   - Are all task steps preserved?
   - Are all rules/constraints included?
   - Is the output JSON schema correct?
   - Are efficiency guidelines present?
   - Are any important details missing?

4. **Document differences** in a comparison table

## VERIFICATION CHECKLIST

### ci-identify-plan (was ci-validate-plan)
- [ ] Database schema documentation preserved
- [ ] SQL query examples preserved
- [ ] Confidence threshold (>80%) mentioned
- [ ] Plan update instructions included
- [ ] Output JSON schema matches (note: filename changed to ci-identify-result.json)

### ci-review-plan (merged with verify-implementation)
- [ ] Deliverables checking from verify-implementation preserved
- [ ] Outcome classification preserved (proceed/pause/proceed_with_review/verified)
- [ ] Efficiency rules present (parallel Glob/Grep)
- [ ] Blocking vs deferrable issues distinction
- [ ] "Write output early" emphasis preserved
- [ ] Output JSON includes deliverables_checked array

### ci-decompose-plan
- [ ] Complexity classification (simple: 1-2, complex: 3+) preserved
- [ ] Hierarchical naming system fully documented
- [ ] Collision prevention steps included
- [ ] Auto-escalation triggers (GUI, image processing) mentioned
- [ ] Parent plan move to decomposed/ folder instruction

### ci-execute-plan
- [ ] TDD discipline steps (RED/GREEN/COMMIT) preserved
- [ ] Environment notes (Linux paths, venv activation)
- [ ] Commit format template included
- [ ] Status values (completed/partial/failed) documented
- [ ] Error field documentation for failures

## OUTPUT REQUIRED

Create a verification report:

```markdown
# CI Command Extraction Verification Report

## Summary
- Commands verified: 4/4
- Issues found: [count]
- Status: [PASS/NEEDS_FIXES]

## Changes from Original
1. `ci-validate-plan` → `ci-identify-plan` (renamed for clarity)
2. `ci-verify-implementation` merged into `ci-review-plan` (eliminated redundancy)

## Detailed Comparison

### ci-identify-plan
| Aspect | Original | Extracted | Match |
|--------|----------|-----------|-------|
| Task steps | ✓ | ✓ | ✓ |
| DB schema | ✓ | ✓ | ✓ |
| ... | ... | ... | ... |

**Issues:** [None / List of issues]

[Continue for each command...]

## Recommendations
[Any suggested fixes or improvements]
```

Write this report to `.claude/data/ci-command-verification-report.md`

## IMPORTANT

- Be thorough - missing logic could break CI automation
- Note any ADDITIONS in the commands (acceptable if they improve clarity)
- Flag any REMOVALS or changes to logic (critical to fix)
- The merge of verify-implementation into review-plan is intentional - verify both sets of logic are present
