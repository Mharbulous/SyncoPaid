# Tree Visualization Tool - User Guide

**Script:** `tree-view.py`
**Purpose:** Generate ASCII/markdown visualizations of your story tree database

## Quick Start

```bash
# View entire tree with capacity and status
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii

# View specific subtree
python .claude/skills/story-tree/tree-view.py --root 1 --show-capacity --force-ascii

# Filter by status
python .claude/skills/story-tree/tree-view.py --status concept --show-capacity --force-ascii

# Get full help
python .claude/skills/story-tree/tree-view.py --help
```

**Windows users:** Always include `--force-ascii` to avoid Unicode encoding errors.

---

## Status Symbols

| Status | Symbol | Meaning |
|--------|--------|---------|
| concept | `.` | Idea, not yet approved |
| approved | `v` | Human reviewed and approved |
| rejected | `x` | Human reviewed and rejected |
| planned | `o` | Implementation plan created |
| queued | `@` | Plan ready, dependencies met |
| active | `O` | Currently being worked on |
| in-progress | `D` | Partially complete |
| bugged | `!` | In need of debugging |
| implemented | `+` | Complete/done |
| ready | `#` | Production ready |
| deprecated | `-` | No longer relevant |
| infeasible | `0` | Couldn't build it |

### Capacity Format

`[children/capacity]` after each node title:
- `[0/5]` = empty, needs stories
- `[3/4]` = 75% full
- `[4/4]` = at capacity

---

## Troubleshooting

### Error: "Database error: no such table: story_nodes"

**Cause:** Database doesn't exist or is corrupted

**Solution:**
```bash
ls -lh .claude/data/story-tree.db
# If 0 bytes, reinitialize: "Initialize story tree"
```

### Error: "Could not find story-tree.db"

**Solution:** Specify path explicitly:
```bash
python .claude/skills/story-tree/tree-view.py --db /full/path/to/story-tree.db --force-ascii
```

### Error: UnicodeEncodeError on Windows

**Solution:** Add `--force-ascii` flag

### Error: "No nodes found for root 'X'"

**Solution:** List valid node IDs first:
```bash
python .claude/skills/story-tree/tree-view.py --compact --force-ascii
```

### Filtered Results Show "Tree structure unavailable"

**Cause:** Status filter excluded ancestor nodes, so tree structure can't be built. Shows flat list instead.

**This is normal** - use `--compact` for cleaner flat list output.
