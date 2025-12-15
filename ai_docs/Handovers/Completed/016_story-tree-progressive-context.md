# Handover: Story Tree Skill - Progressive Context Optimization

## Task
Continue reviewing `.claude/skills/story-tree/SKILL.md` to identify sections that are rarely used and could be moved to separate files for progressive context loading.

## Context
We just completed v2.4.0 refactoring of the story-tree skill with these changes:

1. **Progressive context disclosure** - Moved rarely-used content to separate files:
   - `lib/initialization.md` - Database init (only needed once per repo)
   - `docs/rationales.md` - Design decisions, version history

2. **Intuitive rules** - Simplified instructions to be self-explanatory:
   - Status filter: blacklist (`concept`, `rejected`, `deprecated`, `infeasible`, `bugged`)
   - Dynamic capacity: `3 + implemented/ready children`

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/story-tree/SKILL.md` | Main skill - **review this for more refactoring** |
| `.claude/skills/story-tree/schema.sql` | SQLite schema (updated to v2.4.0) |
| `.claude/skills/story-tree/lib/initialization.md` | Init procedure (extracted) |
| `.claude/skills/story-tree/docs/rationales.md` | Design decisions (extracted) |
| `.claude/skills/story-tree/tree-view.py` | Tree visualization script |

## Principles Applied
- **Progressive disclosure**: Load context only when needed
- **Self-explanatory rules**: Avoid rationale lookups by making instructions intuitive
- **Single source of truth**: Move content, don't duplicate

## Candidates to Evaluate
Potential sections in SKILL.md that might be rarely used:
- Report Format template (~45 lines)
- Tree Visualization Script usage (~75 lines)
- Export Commands section
- Closure Table Concept explanation (educational, not operational?)

## Approach
Read SKILL.md and identify sections by asking:
1. How often is this section needed during normal operation?
2. Could it be referenced only when that specific command is invoked?
3. Is it educational context vs operational instructions?
