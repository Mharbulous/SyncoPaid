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

**CI Mode Action:** Set `review.outcome = "pause"`, do NOT proceed.

### Deferrable Issues

Can be addressed by post-implementation refactoring:
- Code style preferences
- Minor optimizations
- Naming conventions
- Documentation gaps
- Non-critical edge cases

**CI Mode Action:** Set `review.outcome = "proceed_with_review"`, document decisions and proceed.

## Review Output

### temp-CI-notes.json Update

```python
python -c "
import json

state_file = '.claude/skills/story-execution/temp-CI-notes.json'

# Read existing state (or initialize)
try:
    with open(state_file) as f:
        state = json.load(f)
except FileNotFoundError:
    state = {}

# Update review section
state['review'] = {
    'outcome': 'proceed',  # or 'pause' or 'proceed_with_review'
    'blocking_issues': [],
    'deferrable_issues': [],
    'notes': 'Critical review: No blocking or deferrable issues identified'
}

# Example blocking issue format:
# state['review']['blocking_issues'].append({
#     'description': 'Authentication method not specified',
#     'why_blocking': 'Cannot implement login without knowing OAuth vs JWT vs session',
#     'options': ['A: OAuth 2.0', 'B: JWT tokens', 'C: Session cookies']
# })

# Example deferrable issue format:
# state['review']['deferrable_issues'].append({
#     'description': 'Function naming inconsistent with codebase',
#     'decision': 'Using camelCase to match plan, can rename later',
#     'rationale': 'Plan specifies camelCase, refactoring deferred'
# })

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(json.dumps(state['review'], indent=2))
"
```

## Review Outcomes

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| `proceed` | No issues found | Execute batches |
| `pause` | Blocking issues | Stop, report issues |
| `proceed_with_review` | Deferrable issues documented | Execute batches, flag for review |
