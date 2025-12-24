Scan story-tree database for duplicate, overlapping, or competing concepts.

## CI Mode

CI mode auto-activates when `CI=true` env var is set.
Uses `DEFER_PENDING` for HUMAN_REVIEW cases (sets status to `pending`).

## Execution

Invoke `story-vetting` skill, then:
- Run Phase 1 candidate detection script
- Classify each candidate pair
- Execute automated actions (delete, merge, reject, block)
- In CI: defer scope overlaps to `pending` status
- Report summary of actions taken

## Conflict Types

| Type | Description |
|------|-------------|
| `duplicate` | Essentially the same story |
| `scope_overlap` | One subsumes or partially covers another |
| `competing` | Same problem, different/incompatible approaches |
| `incompatible` | Mutually exclusive approaches |
| `false_positive` | Flagged by heuristics but not actually conflicting |

## Expected Output

```
STORY VETTING COMPLETE
======================

Candidates scanned: N
Actions taken:
  - Deleted: X duplicate concepts
  - Merged: Y concept pairs
  - Rejected: Z competing concepts
  - Blocked: W concepts
  - Skipped: V false positives
  - Human review: U scope overlaps (or "Deferred to pending" in CI)
```

## Constraints

- Only processes stories with `concept` status against other stories
- Parent-child relationships are excluded from conflict detection
- Non-concept vs non-concept pairs are ignored
