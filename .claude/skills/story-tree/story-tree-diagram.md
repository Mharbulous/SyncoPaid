# TimeLawg Story Tree Diagram

This file documents how to generate story tree visualizations. For the current tree structure, run the tree-view.py script.

## Quick Commands

```bash
# Full tree with capacity and status
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii

# Compact view (ID and title only)
python .claude/skills/story-tree/tree-view.py --compact

# Markdown format for documentation
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity

# View specific subtree
python .claude/skills/story-tree/tree-view.py --root 1.2 --depth 2

# Filter by status
python .claude/skills/story-tree/tree-view.py --status implemented
python .claude/skills/story-tree/tree-view.py --status deprecated --exclude-status
```

## Status Legend

| Symbol | Status | Description |
|--------|--------|-------------|
| `*` | active | Product vision (root only) |
| `+` | implemented | Feature complete and working |
| `~` | in-progress | Currently being developed |
| `o` | planned | Approved for development |
| `.` | concept | Idea stage |
| `x` | deprecated | No longer relevant |

**Capacity notation:** `[current/target]` - number of child stories vs. target capacity

## Output Formats

- **ascii** (default): Box-drawing characters with tree structure
- **simple**: Indentation-based, no box characters
- **markdown**: Nested bullet list format

## Data Source

All visualizations are generated from the SQLite database at `.claude/data/story-tree.db`.

For SQL-based queries and analysis, see `lib/tree-analyzer.md`.
