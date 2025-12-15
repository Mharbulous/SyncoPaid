# Handover: Status Context Menu with Designer/Engineer Role Toggle

**Status: COMPLETED**

## Task
Implement a role-based context menu system for Xstory (story-tree explorer). Users toggle between "Designer" and "Engineer" modes, which determines available status transitions when right-clicking story nodes.

## Implementation Summary
- Updated `xstory.py` from 23-status to 21-status system (removed `epic`, `in-progress`; kept `broken`)
- Added `DESIGNER_TRANSITIONS` and `ENGINEER_TRANSITIONS` dictionaries defining role-based status transitions
- Added Designer/Engineer toggle button in the toolbar
- Updated context menu to dynamically show available transitions based on current role
- Context menu header shows current status and role mode
- Note: schema.sql was already aligned with the 21-status system

## Key Files
- **Main UI**: `dev-tools/xstory/xstory.py` - tkinter app with role-based context menu
- **Status definitions**: Same file, lines 16-90 - contains color/status mappings and transition tables
- **Schema**: `.claude/skills/story-tree/references/schema.sql` - already has 21-status system

## Status System (21 statuses)
Reduced from original 23. Removed: `epic` (overlaps with `blocked`), `in-progress` (overlaps with `active`). Renamed: `bugged` → `broken`.

Canonical order:
```
infeasible, rejected, wishlist, concept, refine, deferred, approved, blocked,
planned, queued, broken, paused, active, reviewing, implemented, ready,
polish, released, legacy, deprecated, archived
```

## Transition Tables

### Designer Mode (approval, quality, priority, end-of-life decisions)
| Status | Options |
|--------|---------|
| infeasible | concept, wishlist, archived |
| rejected | concept, wishlist, archived |
| wishlist | concept, rejected, archived |
| concept | approved, rejected, wishlist, refine |
| refine | concept, rejected, wishlist |
| deferred | approved, wishlist, rejected |
| approved | deferred, rejected |
| blocked | deferred |
| planned | deferred, approved |
| paused | deferred |
| reviewing | implemented |
| implemented | ready |
| ready | released, polish |
| polish | ready, released |
| released | polish, legacy |
| legacy | deprecated, released, archived |
| deprecated | archived, legacy |
| archived | deprecated, wishlist |

### Engineer Mode (workflow, blockers, bugs, progress)
| Status | Options |
|--------|---------|
| approved | planned |
| blocked | planned, queued |
| planned | queued, blocked |
| queued | active, blocked, paused, planned |
| broken | active, paused, blocked, queued |
| paused | active, queued, blocked |
| active | reviewing, paused, broken, blocked |
| reviewing | active, broken |
| implemented | reviewing, broken |
| ready | reviewing |
| polish | reviewing |
| released | broken |

## Implementation Requirements
1. Add toggle switch to UI (Designer/Engineer mode)
2. Context menu options vary based on current mode
3. Some statuses have no options in certain modes (e.g., `queued` has no Designer options)
4. Existing note-taking dialog should remain (mandatory for `refine`, optional for others)

## Current Context Menu Behavior
- Only `concept` status currently has transitions implemented
- Other statuses show disabled label with current status
- Uses `QInputDialog` for notes with timestamp appending
- Updates `status`, `notes`, `updated_at` fields in SQLite

## Schema Update
The `schema.sql` CHECK constraint was already aligned with the 21-status system (no changes needed).

## Red Herrings
- `src/syncopaid/` - Unrelated; this is the main SyncoPaid app, not the story-tree tool
- `.claude/skills/story-tree/SKILL.md` - Documents the skill prompt, not the UI implementation
