# Handover: Story-Tree v2 - 23-Status System with Database Migration

## Task
Refactor story-tree skill to support expanded 23-status system with rainbow color scheme. Migrate existing data from v1 database to new schema without data loss.

## Critical Context

**Previous version archived:** `archived/story-tree-v1/` - reference only, do NOT modify
**Working skill location:** `.claude/skills/story-tree/`
**Database locations:**
- Current (v1): `.claude/data/story-tree.db` - preserve data
- New (v2): Create after schema update

## Status System Design (This Session)

### Complete 23-Status List - Rainbow Ordered by Production Proximity

| # | Status | Color | Hex | Unicode | ASCII | Description |
|---|--------|-------|-----|---------|-------|-------------|
| 1 | `infeasible` | Deep Red | `#8B0000` | ∅ | 0 | Cannot be built |
| 2 | `rejected` | Red-Orange | `#FF4500` | ✗ | x | Human rejected |
| 3 | `wishlist` | Orange | `#FF8C00` | ? | W | Rejected for now, may reconsider later |
| 4 | `concept` | Yellow-Orange | `#FFA500` | · | . | Idea, not yet approved |
| 5 | **`refine`** | **Sandy** | **`#FFB347`** | **◈** | **r** | **Concept needs rework before approval** ⭐ NEW |
| 6 | `approved` | Gold | `#FFD700` | ✓ | v | Human approved, not yet planned |
| 7 | `epic` | Light Gold | `#FFDB58` | ◆ | E | Approved but too complex; needs decomposition |
| 8 | `planned` | Khaki | `#F0E68C` | ○ | o | Implementation plan created |
| 9 | `blocked` | Dark Goldenrod | `#B8860B` | ⊗ | X | Planned but blocked by external dependencies ⭐ NEW |
| 10 | `pending` | Light Goldenrod | `#EEE8AA` | ⏸ | = | Approved but intentionally postponed ⭐ NEW |
| 11 | `queued` | Yellow-Green | `#9ACD32` | ◎ | @ | Ready, dependencies met |
| 12 | `bugged` | Goldenrod | `#DAA520` | ⚠ | ! | Needs debugging |
| 13 | `paused` | Dark Khaki | `#BDB76B` | ⏸ | \| | Was active but temporarily on hold ⭐ NEW |
| 14 | `active` | Lime Green | `#32CD32` | ● | O | Currently being worked on |
| 15 | `in-progress` | Medium Spring Green | `#00FA9A` | ◐ | D | Partially complete |
| 16 | `reviewing` | Turquoise | `#40E0D0` | 👁 | R | Implemented, under review/testing ⭐ NEW |
| 17 | `implemented` | Sky Blue | `#4169E1` | ★ | + | Complete/done |
| 18 | `ready` | Blue | `#0000FF` | ✔ | # | Production ready, tested |
| 19 | **`polish`** | **Cobalt Blue** | **`#0047AB`** | **◇** | **p** | **Final refinements before release** ⭐ NEW |
| 20 | `released` | Royal Blue | `#4169E1` | 🚀 | ^ | Deployed to production ⭐ NEW |
| 21 | **`legacy`** | **Indigo** | **`#4B0082`** | **◊** | **L** | **Superseded, still works, dependencies need checking** ⭐ NEW |
| 22 | `deprecated` | Dark Violet | `#9400D3` | ⊘ | - | Dependencies checked, ready for removal |
| 23 | `archived` | Purple | `#800080` | 📦 | A | Removed from production ⭐ NEW |

**Key Insights:**
1. **Two Refinement Stages:**
   - **`refine`** (early) - Concept/idea needs rework before approval
   - **`polish`** (late) - Working feature needs final touches before release

2. **End-of-Life Progression:**
   - **`legacy`** - Superseded but working, dependencies need checking
   - **`deprecated`** - Dependencies migrated, ready for removal
   - **`archived`** - Removed from production

### Color Zones

```
🔴 Red (Can't/Won't): infeasible → rejected → wishlist
🟡 Orange-Yellow (Concept): concept → refine → approved → epic
🟡 Yellow (Planning): planned → blocked → pending
🟢 Yellow-Green (Ready): queued → bugged → paused
🟢 Green (Development): active → in-progress
💙 Cyan-Blue (Testing): reviewing → implemented
💙 Blue (Production): ready → polish → released
🟣 Violet (Post-Production): legacy → deprecated → archived
```

## Files to Modify

### 1. Schema (PRIMARY)
**File:** `.claude/skills/story-tree/references/schema.sql`
- Update status CHECK constraint (line ~21-36) to include 23 statuses
- Consider adding `color` column to story_nodes table for UI support
- Bump version to 3.0.0

### 2. Main Skill
**File:** `.claude/skills/story-tree/SKILL.md`
- Update status documentation with new 23-status table
- Add color scheme documentation
- Update default status logic if needed

### 3. Tree View Script
**File:** `.claude/skills/story-tree/scripts/tree-view.py`
- Add Unicode/ASCII symbols for 9 new statuses
- Add color output support (consider `colorama` or ANSI codes)
- Update status legend

### 4. Xstory (Dev Tool)
**File:** `dev-tools/xstory/xstory.py`
- Add color-coded status display using hex values
- Update filter options for new statuses
- Consider status grouping by color zone

## Migration Strategy

### Option A: Schema Migration Script (Recommended)
1. Create `scripts/migrate_v1_to_v2.py`
2. Read from `.claude/data/story-tree.db` (v1)
3. Map old statuses to new (most are 1:1)
4. Create `.claude/data/story-tree-v2.db`
5. Populate with migrated data
6. Backup v1, rename v2 to primary

### Option B: SQL Migration
1. Copy `.claude/data/story-tree.db` to `story-tree-backup.db`
2. Use SQLite ALTER TABLE if possible (may not work with CHECK constraint)
3. Or recreate tables with new schema and INSERT FROM old

### Status Mapping for Migration
```
v1 → v2 (unchanged):
  concept, approved, epic, rejected, wishlist, planned, queued,
  active, in-progress, bugged, implemented, ready, deprecated

v1 → v2 (new defaults):
  infeasible (keep)

New statuses with no v1 equivalent:
  refine, blocked, pending, paused, reviewing, polish, released, legacy, archived
  (These won't exist in migrated data)
```

## Red Herrings (Don't Waste Time)

- ❌ `ai_docs/story-tree-skill-overview.md` - High-level only, no implementation details
- ❌ `ai_docs/Plans/story-tree-ascii-visualizer.md` - Old plan, not current
- ❌ `.claude/commands/generate-stories.md` - Just invokes skill, not skill code
- ❌ `dev-tools/xstory/xstory-1-0.py` - Old version
- ❌ `dev-tools/xstory/xstory-1-1.py` - Old version

## Key Reference Files

### Essential
- `.claude/skills/story-tree/references/schema.sql` - Canonical schema
- `.claude/skills/story-tree/SKILL.md` - Main skill logic
- `ai_docs/Handovers/015_story-tree-status-expansion.md` - Previous status expansion (6→14)
- `ai_docs/Handovers/017_story-tree-epic-wishlist-status.md` - Epic/wishlist addition

### Helpful
- `.claude/skills/story-tree/references/sql-queries.md` - Common query patterns
- `.claude/skills/story-tree/scripts/tree-view.py` - Status visualization
- `ai_docs/Handovers/020_story-tree-explorer-treeview-display.md` - Latest explorer work

## Research Sources

### Thesaurus Research (for status naming)
- [Merriam-Webster: Revising](https://www.merriam-webster.com/thesaurus/revising) - Comprehensive synonyms
- [Merriam-Webster: Refining](https://www.merriam-webster.com/thesaurus/refining) - Polish, enhance, improve
- [Power Thesaurus: Almost Ready](https://www.powerthesaurus.org/almost_ready/synonyms) - Near-completion terms
- [WordHippo: Revising Synonyms](https://www.wordhippo.com/what-is/another-word-for/revising.html) - Alternative phrasing

### Design Decisions Made
1. **Rejected "reworking"** - Too heavy, implies major overhaul
2. **Rejected "iterating"** - Too technical/jargon
3. **Chose "refine"** - Clear, positive, appropriate for concepts
4. **Chose "polish"** - Distinct from refine, implies near-completion
5. **Added "legacy"** - End-of-life stage between released and deprecated
6. **Rainbow ordering** - Production proximity determines color (red=furthest, blue=closest, violet=past)

### End-of-Life Path (Key Insight)
```
released → legacy → deprecated → archived
```
- **`legacy`** - Superseded by newer version, still works, but dependencies need to be checked/migrated
- **`deprecated`** - Dependencies checked/migrated, officially marked for removal, ready to remove
- **`archived`** - Removed from production entirely

## Implementation Checklist

- [ ] Update schema.sql with 23-status CHECK constraint
- [ ] Consider adding `color` column to story_nodes
- [ ] Update SKILL.md documentation
- [ ] Add new status symbols to tree-view.py
- [ ] Implement color output in tree-view.py
- [ ] Update xstory.py with color coding
- [ ] Create migration script
- [ ] Test migration on backup database
- [ ] Run migration on production database
- [ ] Verify no data loss
- [ ] Test skill with new statuses
- [ ] Update any queries that filter by status

## Notes

- User explicitly wants to preserve v1 data during migration
- v1 skill archived at `archived/story-tree-v1/` (read-only reference)
- This is a major version bump (v2.x → v3.0) due to schema changes
- Color scheme should be configurable in case user wants to customize
- Consider backward compatibility for any external tools reading the database
