# Review Plan for Execution

Review a plan document to determine if it's ready for CI execution, including verification that it hasn't already been implemented.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024_feature.md`)

---

## YOUR TASK

1. Read the plan file at `$ARGUMENTS` completely
2. Identify the TOP 3-5 KEY deliverables (new files, critical functions)
3. Use parallel Glob/Grep calls to check if they already exist
4. If implementation exists → outcome "verified"
5. If not implemented, check for blocking issues
6. Write the result file AS SOON AS you have a decision

## EFFICIENCY RULES (CRITICAL)

- Use Glob/Grep in PARALLEL for speed
- Stop searching once you have enough evidence (3-5 checks is usually enough)
- WRITE THE OUTPUT FILE AS SOON AS you have a decision
- Prioritize: new files > new functions > config changes > minor modifications
- Don't exhaustively verify every detail - focus on KEY deliverables

## OUTCOME CLASSIFICATION

### Already Implemented → outcome: "verified"
- Core files/functions from the plan already exist
- Test files already exist with passing tests
- **Recommendation:** Archive the plan, skip execution

### Blocking Issues → outcome: "pause"
- Security implications, breaking changes, missing critical info
- Dependencies not implemented
- **Recommendation:** Human review required before proceeding

### Minor Issues → outcome: "proceed_with_review"
- Style issues, minor gaps (document and proceed)
- **Recommendation:** Execute but flag for post-execution review

### Ready to Execute → outcome: "proceed"
- Plan is clear, work has NOT been done yet
- No blocking issues found
- **Recommendation:** Execute immediately

## OUTPUT

Write to `.claude/skills/story-execution/ci-review-result.json`:

```json
{
  "outcome": "proceed|pause|proceed_with_review|verified",
  "deliverables_checked": [
    {"item": "src/feature.py", "found": false, "location": null},
    {"item": "tests/test_feature.py", "found": false, "location": null}
  ],
  "blocking_issues": [],
  "deferrable_issues": [],
  "notes": "Brief summary of findings"
}
```

## HUMAN-READABLE OUTPUT

After writing the JSON file, print a summary:

```
## Review Result: [OUTCOME]

**Plan:** [filename]
**Recommendation:** [archive/pause/execute/execute with review]

### Deliverables Checked
| Item | Found | Location |
|------|-------|----------|
| src/feature.py | ✗ | - |
| tests/test_feature.py | ✗ | - |

### Blocking Issues
- [if any, otherwise "None"]

### Deferrable Issues
- [if any, otherwise "None"]

### Summary
[Brief explanation of the decision]
```
