# Story Tree ASCII Visualizer - Implementation Plan

## Overview

A Python script to generate ASCII tree diagrams from the story-tree SQLite database, providing human-readable hierarchical visualizations with customizable filtering and formatting options.

## Database Context

- **Location**: `.claude\data\story-tree.db`
- **Schema**: Closure table pattern with `story_nodes` and `story_tree` tables
- **Key Fields**: `id`, `title`, `status`, `capacity`, `description`
- **Status Values**: `concept`, `planned`, `in-progress`, `implemented`, `deprecated`, `active`

## Script Location

`.claude\skills\story-tree\tree-view.py`

## Command-Line Interface

```bash
python tree-view.py [OPTIONS]

Options:
  --root ID          Start tree from specific node (default: "root")
  --depth N          Maximum depth to display (default: unlimited)
  --status STATUS    Filter by status (can specify multiple: --status implemented --status planned)
  --exclude-status   Exclude specified statuses instead of including
  --compact          Minimal output: ID and title only
  --verbose          Include description (truncated to 60 chars)
  --show-capacity    Show capacity as [children/capacity]
  --show-status      Show status indicator
  --no-color         Disable ANSI color codes
  --format FORMAT    Output format: ascii (default), simple, markdown
  --db PATH          Custom database path
  --help             Show help message
```

## Output Formats

### ASCII Format (default)
```
SyncoPaid [6/10] ●
├── 1 Window activity tracking [4/4] ✓
│   ├── 1.1 Poll active window every second ✓
│   ├── 1.2 Extract application name from process ✓
│   ├── 1.3 Merge consecutive identical events ✓
│   └── 1.4 Detect system idle state ✓
├── 2 Periodic screenshot capture [5/5] ✓
│   └── ...
└── 3 Action-based screenshot capture [4/4] ✓
    └── ...
```

### Compact Format
```
root: SyncoPaid
  1: Window activity tracking
    1.1: Poll active window every second
    1.2: Extract application name from process
```

### Markdown Format
```markdown
- **SyncoPaid** [6/10] `active`
  - **1 Window activity tracking** [4/4] `implemented`
    - 1.1 Poll active window every second `implemented`
```

## Status Indicators

| Status | Symbol | Color (ANSI) |
|--------|--------|--------------|
| active | ● | Blue |
| implemented | ✓ | Green |
| in-progress | ◐ | Yellow |
| planned | ○ | Cyan |
| concept | · | White |
| deprecated | ✗ | Gray |

## Implementation Tasks

### Task 1: Database Query Module
Create efficient queries using the closure table:

```python
def get_tree_data(db_path, root_id='root', max_depth=None, statuses=None):
    """
    Query all nodes in subtree with their depth and child counts.
    Returns list of dicts with: id, title, description, status, capacity,
                                child_count, depth, parent_id
    """
```

Key SQL:
```sql
SELECT
    s.id, s.title, s.description, s.status, s.capacity,
    st.depth,
    (SELECT COUNT(*) FROM story_tree WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT st2.ancestor_id FROM story_tree st2
     WHERE st2.descendant_id = s.id AND st2.depth = 1) as parent_id
FROM story_nodes s
JOIN story_tree st ON s.id = st.descendant_id
WHERE st.ancestor_id = :root_id
ORDER BY st.depth, s.id;
```

### Task 2: Tree Builder
Convert flat query results into nested tree structure:

```python
class TreeNode:
    def __init__(self, id, title, status, capacity, child_count, depth, description=''):
        self.id = id
        self.title = title
        self.status = status
        self.capacity = capacity
        self.child_count = child_count
        self.depth = depth
        self.description = description
        self.children = []

def build_tree(rows) -> TreeNode:
    """Build tree from flat database rows."""
```

### Task 3: ASCII Renderer
Generate tree lines with proper box-drawing characters:

```python
def render_ascii(node, options) -> list[str]:
    """
    Render tree to list of strings.
    Uses: ├── │ └── for tree branches
    """
```

Box-drawing characters:
- Branch: `├── `
- Last branch: `└── `
- Vertical line: `│   `
- Empty: `    `

### Task 4: Color Support
ANSI escape codes for terminal colors:

```python
COLORS = {
    'active': '\033[94m',      # Blue
    'implemented': '\033[92m', # Green
    'in-progress': '\033[93m', # Yellow
    'planned': '\033[96m',     # Cyan
    'concept': '\033[97m',     # White
    'deprecated': '\033[90m',  # Gray
    'reset': '\033[0m'
}
```

### Task 5: CLI Argument Parser
Use `argparse` for command-line interface:

```python
def parse_args():
    parser = argparse.ArgumentParser(
        description='Display story tree as ASCII diagram'
    )
    # Add all options from CLI spec above
    return parser.parse_args()
```

### Task 6: Main Entry Point

```python
def main():
    args = parse_args()

    # Resolve database path
    db_path = args.db or find_default_db()

    # Query data
    rows = get_tree_data(db_path, args.root, args.depth, args.status)

    # Build tree
    tree = build_tree(rows)

    # Render output
    options = RenderOptions(
        compact=args.compact,
        verbose=args.verbose,
        show_capacity=args.show_capacity,
        show_status=args.show_status,
        use_color=not args.no_color,
        format=args.format
    )

    lines = render(tree, options)
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
```

## File Structure

```
.claude/skills/story-tree/
├── tree-view.py          # Main script (new)
├── schema.sql
├── SKILL.md
└── ...
```

## Dependencies

- `sqlite3` (stdlib)
- `argparse` (stdlib)
- No external dependencies required

## Example Usage

```bash
# Full tree with capacity and status
python tree-view.py --show-capacity --show-status

# Only implemented stories, compact view
python tree-view.py --status implemented --compact

# Subtree from node 2, max 2 levels deep
python tree-view.py --root 2 --depth 2

# Markdown output for documentation
python tree-view.py --format markdown > tree.md

# Everything except deprecated
python tree-view.py --status deprecated --exclude-status
```

## Integration with Skill

The skill file (`SKILL.md`) can reference this script:

```markdown
## Tree Visualization
For ASCII tree output, run:
\`\`\`bash
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status
\`\`\`
```

## Testing

Manual verification:
1. Run with default options - should show full tree
2. Test `--depth 1` - should show only root's direct children
3. Test `--root 1` - should show subtree
4. Test `--status implemented` - should filter correctly
5. Test `--format markdown` - should produce valid markdown
6. Test `--no-color` - should have no ANSI codes
