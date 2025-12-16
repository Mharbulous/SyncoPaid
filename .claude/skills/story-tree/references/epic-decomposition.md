# Epic Decomposition

## Key Rules

1. **Child stories inherit nothing** - Parent approval does NOT cascade:
   - Each child needs separate human review
   - Children may be rejected even if parent was approved
   - Prevents scope creep from approved epics

2. **Excluded from generation** - `epic` is excluded from priority algorithm because epic nodes already have approved scope and need decomposition, not more children

## `wishlist` vs `rejected`

- `wishlist`: "Not now, but maybe later" - retained for future consideration
- `rejected`: "No, this doesn't fit" - excluded permanently
