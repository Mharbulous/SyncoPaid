Create implementation plans for approved story-nodes.

## Arguments

$Arguments

## CI Mode

CI mode auto-activates when `CI=true` env var is set or trigger includes "(ci)".
Uses compact template (~60% token reduction).

## Argument Handling

- **Specific ID(s)**: `/plan-story 1.8.2` or `/plan-story 1.2 1.3 1.4`
- **Count**: `/plan-story 3` → plan top 3 priority stories
- **No arguments**: Plan single highest-priority approved story

## Constraints

- Maximum 5 plans per invocation
- Only stories with `stage = 'approved'` (not held or disposed)
- Skip non-existent/non-approved IDs with error message, continue with remaining
- If fewer approved stories than requested, plan all available

## Execution

Invoke `story-planning` skill, then:
- Process stories sequentially
- Create separate plan files
- Update each story's stage to `planned`
- Summary report at end listing all plans created
