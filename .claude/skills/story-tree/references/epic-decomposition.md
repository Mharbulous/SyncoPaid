# Epic Decomposition

## Key Rules

1. **Child stories inherit nothing** - Parent approval does NOT cascade:
   - Each child needs separate human review
   - Children may be rejected even if parent was approved
   - Prevents scope creep from approved epics

2. **Excluded from generation** - Parent/epic nodes (identified by `capacity > 5` or children) are excluded from priority algorithm. They should have `stage >= 'approved'` and focus on decomposition.

## `wishlist` vs `rejected`

- `wishlist` (hold_reason): "Not now, but maybe later" - indefinite hold, can be revived when priorities change
- `rejected` (disposition): "No, this doesn't fit" - terminal state, excluded permanently
