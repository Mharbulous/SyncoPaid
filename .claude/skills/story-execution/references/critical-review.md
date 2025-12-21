# Critical Review

Before executing any code, review the plan critically to identify issues.

## Process

1. Read the entire plan
2. Quick check: Does the plan's KEY deliverable already exist? (1-2 targeted searches)
3. Make a decision and WRITE THE OUTPUT FILE IMMEDIATELY
4. Only do deeper analysis if initial check is inconclusive

## Efficiency Guidelines (CI Mode)

- Use Glob/Grep in PARALLEL for speed
- Stop searching once you have enough evidence (2-3 files is usually enough)
- WRITE THE OUTPUT FILE AS SOON AS you have a decision
- Don't exhaustively verify every detail - focus on KEY deliverables

## Issue Classification

### Blocking Issues

Require human decision before implementation:
- Architectural choices with significant trade-offs
- Security implications (auth, data exposure, permissions)
- Breaking changes to existing functionality
- Missing critical information
- Conflicting requirements

**CI Mode Action:** Set `outcome = "pause"`, do NOT proceed.

### Deferrable Issues

Can be addressed by post-implementation refactoring:
- Code style preferences
- Minor optimizations
- Naming conventions
- Documentation gaps
- Non-critical edge cases

**CI Mode Action:** Set `outcome = "proceed_with_review"`, document decisions and proceed.

## Review Output

Write to `.claude/skills/story-execution/ci-review-result.json`:

```json
{
  "outcome": "proceed",
  "blocking_issues": [],
  "deferrable_issues": [],
  "notes": "Critical review: No blocking or deferrable issues identified"
}
```

### Example: Blocking Issue

```json
{
  "outcome": "pause",
  "blocking_issues": [
    {
      "description": "Authentication method not specified",
      "why_blocking": "Cannot implement login without knowing OAuth vs JWT vs session",
      "options": ["A: OAuth 2.0", "B: JWT tokens", "C: Session cookies"]
    }
  ],
  "deferrable_issues": [],
  "notes": "Plan paused due to missing auth specification"
}
```

### Example: Deferrable Issue

```json
{
  "outcome": "proceed_with_review",
  "blocking_issues": [],
  "deferrable_issues": [
    {
      "description": "Function naming inconsistent with codebase",
      "decision": "Using camelCase to match plan, can rename later",
      "rationale": "Plan specifies camelCase, refactoring deferred"
    }
  ],
  "notes": "Proceeding with noted style inconsistency"
}
```

## Review Outcomes

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| `verified` | Already implemented | Archive plan, skip execution |
| `proceed` | No issues found | Continue to decompose stage |
| `pause` | Blocking issues | Stop, report issues |
| `proceed_with_review` | Deferrable issues documented | Continue, flag for review |

### Example: Already Implemented

```json
{
  "outcome": "verified",
  "blocking_issues": [],
  "deferrable_issues": [],
  "notes": "Core implementation already exists: database.py has cmdline column, tests passing"
}
```
