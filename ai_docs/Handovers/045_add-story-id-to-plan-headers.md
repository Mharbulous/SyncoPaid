# Task: Add Story ID to Plan File Headers

## Objective
Update `.claude/skills/story-planning/SKILL.md` so that when it generates plan files, the Story ID is always included in the header section.

## Key Files
- `.claude/skills/story-planning/SKILL.md` - The skill to modify
- `.claude/data/plans/*.md` - Example output files (none currently have Story IDs)

## Context
The story-execution skill now has Step 1.5a that detects "orphan plans" - plans lacking a Story ID or whose ID isn't in the database. These get archived to `.claude/data/plans/orphan/` and skipped.

Currently, ALL 46 plan files lack Story IDs, so they'd all be flagged as orphans.

## Required Change
Add to the plan file template/output format a header field like:
```
**Story ID:** X.Y.Z
```

The story-planning skill receives a story ID as input (either from user or from database lookup). Ensure this ID gets written into the generated plan file header.

## Pattern to Match
The story-execution skill extracts Story ID using this regex:
```python
re.search(r'\*?\*?Story ID\*?\*?:?\s*(\d+(?:\.\d+)*)', content)
```

So valid formats include:
- `Story ID: 1.2.3`
- `**Story ID:** 1.2.3`
- `**Story ID**: 1.2.3`

## Verification
After changes, a newly generated plan should include the Story ID in a way that Step 1.5a can extract it and verify it exists in `story-tree.db`.
