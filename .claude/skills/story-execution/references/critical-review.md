# Critical Review

Before executing any code, review the plan critically to identify issues.

## Process

1. Read the entire plan
2. Check prerequisites (dependencies implemented, baseline tests pass)
3. Identify any questions, concerns, or ambiguities
4. Classify concerns as blocking or deferrable

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
| `proceed` | No issues found | Continue to decompose stage |
| `pause` | Blocking issues | Stop, report issues |
| `proceed_with_review` | Deferrable issues documented | Continue, flag for review |
