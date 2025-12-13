# Handover: Story-Tree Epic/Wishlist Status Support

**Task:** Update story-tree skill to support epic decomposition workflow

## Add Two New Status Values

- `epic` - Approved story too complex for single implementation; needs decomposition into smaller `concept` stories before planning
- `wishlist` - Rejected for now but may reconsider later

## Files to Modify

1. **Schema:** `.claude\skills\story-tree\references\schema.sql`
   - Add `epic` and `wishlist` to status CHECK constraint (line ~15)

2. **Main skill:** `.claude\skills\story-tree\story-tree.skill.md`
   - Update status documentation
   - Add new reference file mention

3. **Tree view script:** `.claude\skills\story-tree\scripts\tree-view.py`
   - Add symbols for new statuses (suggest: `epic` = `◆`/`E`, `wishlist` = `?`/`W`)

4. **Create new reference:** `.claude\skills\story-tree\references\epic-decomposition.md`
   - Document workflow: when epic detected → decompose into `concept` children
   - Clarify: child stories inherit nothing automatic from parent approval
   - Consider: should epics move closer to root in tree hierarchy?

## Key Context from Prior Session

- Reviewed 6 approved stories in implementation order
- Story 1.8.4 was decomposed into 4 children (1.8.4.1-1.8.4.4) with `concept` status
- This triggered realization that decomposition workflow needs formal documentation
- User preference: KISS principle throughout

## File Locations

- **Database:** `.claude\data\story-tree.db`
- **Skill root:** `.claude\skills\story-tree\`

## Not Relevant

The `references\sql-queries.md` and `references\common-mistakes.md` files don't need updates for this change.
