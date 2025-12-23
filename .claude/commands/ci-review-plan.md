# Review Plan for Execution

Review a plan document to determine if it's ready for CI execution.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024_feature.md`)

---

## YOUR TASK

1. Read the plan file at `$ARGUMENTS` completely
2. Quick check: Does the plan's KEY deliverable already exist? (1-2 targeted searches max)
3. Make a decision and write the output
4. Only do deeper analysis if initial check is inconclusive

## EFFICIENCY RULES (CRITICAL)

- Use Glob/Grep in PARALLEL for speed
- Stop searching once you have enough evidence (2-3 files is usually enough)
- WRITE THE OUTPUT FILE AS SOON AS you have a decision
- Don't exhaustively verify every detail - focus on KEY deliverables

## OUTCOME CLASSIFICATION

### Already Implemented → outcome: "verified"
- Core files/functions from the plan already exist
- Test files already exist with passing tests

### Blocking Issues → outcome: "pause"
- Security implications, breaking changes, missing critical info
- Dependencies not implemented

### Minor Issues → outcome: "proceed_with_review"
- Style issues, minor gaps (document and proceed)

### Ready to Execute → outcome: "proceed"
- Plan is clear, work has NOT been done yet

## OUTPUT

Write to `.claude/skills/story-execution/ci-review-result.json`:

```json
{
  "outcome": "proceed|pause|proceed_with_review|verified",
  "blocking_issues": [],
  "deferrable_issues": [],
  "notes": "Brief summary"
}
```

After writing the JSON file, also print a human-readable summary:

```
## Review Result: [OUTCOME]

**Plan:** [filename]
**Notes:** [brief explanation]

### Blocking Issues
- [if any]

### Deferrable Issues
- [if any]
```
