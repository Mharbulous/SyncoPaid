# Verify CI Command Extraction

Verify that the extracted CI slash commands preserve all logic from the original workflow.

---

## CONTEXT

The execute-stories.yml workflow (2292 lines) contained 5 embedded Claude prompts that have been
extracted into reusable slash commands. This verification ensures no logic was lost or changed.

## FILES TO COMPARE

### Original Workflow (Source of Truth)
`.claude/deprecated/execute-stories.yml`

### Extracted Commands
| Command | Lines in Original | Purpose |
|---------|-------------------|---------|
| `.claude/commands/ci-validate-plan.md` | 386-482 | Match plan to story database |
| `.claude/commands/ci-verify-implementation.md` | 631-700 | Check if implementation exists |
| `.claude/commands/ci-review-plan.md` | 880-939 | Critical review, decide outcome |
| `.claude/commands/ci-decompose-plan.md` | 1002-1135 | Assess complexity, split plans |
| `.claude/commands/ci-execute-plan.md` | 1378-1457 | Execute TDD steps |

## YOUR TASK

For EACH of the 5 commands:

1. **Read the original prompt** from the deprecated workflow file (use the line ranges above)
2. **Read the extracted command** file
3. **Compare systematically:**
   - Are all task steps preserved?
   - Are all rules/constraints included?
   - Is the output JSON schema identical?
   - Are efficiency guidelines present?
   - Are any important details missing?

4. **Document differences** in a comparison table

## VERIFICATION CHECKLIST

For each command, verify:

### ci-validate-plan
- [ ] Database schema documentation preserved
- [ ] SQL query examples preserved
- [ ] Confidence threshold (>80%) mentioned
- [ ] Plan update instructions included
- [ ] Output JSON schema matches

### ci-verify-implementation
- [ ] Efficiency guidelines preserved (parallel Glob/Grep)
- [ ] 3-5 key deliverables focus mentioned
- [ ] Verification criteria (PASS/PARTIAL/FAIL) documented
- [ ] Recommendation values (archive/execute/manual_review) correct
- [ ] "Write output early" emphasis preserved

### ci-review-plan
- [ ] Outcome classification preserved (proceed/pause/proceed_with_review/verified)
- [ ] Efficiency rules present
- [ ] Blocking vs deferrable issues distinction
- [ ] Output JSON schema matches

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
- Commands verified: 5/5
- Issues found: [count]
- Status: [PASS/NEEDS_FIXES]

## Detailed Comparison

### ci-validate-plan
| Aspect | Original | Extracted | Match |
|--------|----------|-----------|-------|
| Task steps | ✓ | ✓ | ✓ |
| DB schema | ✓ | ✓ | ✓ |
| ... | ... | ... | ... |

**Issues:** [None / List of issues]

### ci-verify-implementation
[Same table format]

### ci-review-plan
[Same table format]

### ci-decompose-plan
[Same table format]

### ci-execute-plan
[Same table format]

## Recommendations
[Any suggested fixes or improvements]
```

Write this report to `.claude/data/ci-command-verification-report.md`

## IMPORTANT

- Be thorough - missing logic could break CI automation
- Note any ADDITIONS in the commands (acceptable if they improve clarity)
- Flag any REMOVALS or changes to logic (critical to fix)
- The commands may have improved formatting - that's fine as long as logic is preserved
