#!/usr/bin/env python3
"""
Story Tree ASCII Visualizer

Generates ASCII tree diagrams from the story-tree SQLite database.
"""

import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


# ANSI color codes
COLORS = {
    'concept': '\033[97m',      # White
    'approved': '\033[96m',     # Cyan
    'planned': '\033[96m',      # Cyan
    'active': '\033[94m',       # Blue
    'reviewing': '\033[93m',    # Yellow
    'verifying': '\033[93m',    # Yellow
    'implemented': '\033[92m',  # Green
    'ready': '\033[92m',        # Green
    'polish': '\033[95m',       # Magenta
    'released': '\033[92m',     # Green
    'held': '\033[93m',         # Yellow (for any hold_reason)
    'disposed': '\033[90m',     # Gray (for any disposition)
    'reset': '\033[0m'
}

# Status symbols
SYMBOLS = {
    'concept': '·',
    'approved': '○',
    'planned': '○',
    'active': '●',
    'reviewing': '◐',
    'verifying': '◑',
    'implemented': '✓',
    'ready': '✓',
    'polish': '◇',
    'released': '✓',
    'held': '⊗',
    'disposed': '✗'
}


@dataclass
class RenderOptions:
    """Options for rendering the tree."""
    compact: bool = False
    verbose: bool = False
    show_capacity: bool = False
    show_status: bool = False
    use_color: bool = True
    format: str = 'ascii'


class TreeNode:
    """Represents a node in the story tree."""

    def __init__(self, id: str, title: str, stage: str, capacity: Optional[int],
                 child_count: int, depth: int, description: str = '',
                 hold_reason: Optional[str] = None, disposition: Optional[str] = None):
        self.id = id
        self.title = title
        self.stage = stage
        self.capacity = capacity
        self.child_count = child_count
        self.depth = depth
        self.description = description
        self.hold_reason = hold_reason
        self.disposition = disposition
        self.children: List[TreeNode] = []

    @property
    def effective_status(self) -> str:
        """Get the effective status for display purposes."""
        if self.disposition:
            return 'disposed'
        elif self.hold_reason:
            return 'held'
        else:
            return self.stage


def find_default_db() -> Path:
    """Find the default story-tree database."""
    # Try relative path first
    rel_path = Path('.claude/data/story-tree.db')
    if rel_path.exists():
        return rel_path

    # Try absolute path from script location
    script_dir = Path(__file__).parent
    abs_path = script_dir / '../../data/story-tree.db'
    if abs_path.exists():
        return abs_path.resolve()

    return rel_path  # Return relative path as fallback


def get_tree_data(db_path: Path, root_id: str = 'root', max_depth: Optional[int] = None,
                  stages: Optional[List[str]] = None, exclude: bool = False) -> List[Dict[str, Any]]:
    """
    Query all nodes in subtree with their depth and child counts.

    Args:
        db_path: Path to the SQLite database
        root_id: Root node ID to start from
        max_depth: Maximum depth to query (None = unlimited)
        stages: List of stages to filter by (None = all)
        exclude: If True, exclude specified stages instead of including

    Returns:
        List of dicts with node data
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build the query - use ? placeholders for consistency
    query = """
        SELECT
            s.id, s.title, s.description, s.stage, s.capacity,
            s.hold_reason, s.disposition,
            st.depth,
            (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
            (SELECT st2.ancestor_id FROM story_paths st2
             WHERE st2.descendant_id = s.id AND st2.depth = 1) as parent_id
        FROM story_nodes s
        JOIN story_paths st ON s.id = st.descendant_id
        WHERE st.ancestor_id = ?
    """

    params = [root_id]

    # Add depth filter
    if max_depth is not None:
        query += " AND st.depth <= ?"
        params.append(max_depth)

    # Add stage filter
    if stages:
        if exclude:
            placeholders = ','.join(['?' for _ in stages])
            query += f" AND s.stage NOT IN ({placeholders})"
        else:
            placeholders = ','.join(['?' for _ in stages])
            query += f" AND s.stage IN ({placeholders})"
        params.extend(stages)

    query += " ORDER BY st.depth, s.id"

    # Execute with proper parameter binding
    cursor.execute(query, params)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return rows


def build_tree(rows: List[Dict[str, Any]]) -> Optional[TreeNode]:
    """Build tree from flat database rows."""
    if not rows:
        return None

    # Create all nodes
    nodes = {}
    for row in rows:
        node = TreeNode(
            id=row['id'],
            title=row['title'],
            stage=row['stage'],
            capacity=row['capacity'],
            child_count=row['child_count'],
            depth=row['depth'],
            description=row['description'] or '',
            hold_reason=row.get('hold_reason'),
            disposition=row.get('disposition')
        )
        nodes[row['id']] = node

    # Build parent-child relationships
    root = None
    for row in rows:
        node = nodes[row['id']]
        parent_id = row.get('parent_id')

        if parent_id and parent_id in nodes:
            nodes[parent_id].children.append(node)
        elif row['depth'] == 0:
            root = node

    return root


def render_ascii(node: TreeNode, options: RenderOptions, prefix: str = '', is_last: bool = True) -> List[str]:
    """
    Render tree to list of strings using ASCII box-drawing characters.

    Args:
        node: The node to render
        options: Rendering options
        prefix: Prefix for the current line (used in recursion)
        is_last: Whether this is the last child (affects branch character)

    Returns:
        List of strings representing the tree
    """
    lines = []

    # Build the node line
    if node.depth == 0:
        # Root node - no prefix
        line = ''
    else:
        # Child node - add branch characters
        branch = '└── ' if is_last else '├── '
        line = prefix + branch

    # Add node ID (for non-root or compact mode)
    if options.compact or node.depth > 0:
        line += f"{node.id}: "

    # Add title
    line += node.title

    # Add capacity
    if options.show_capacity and node.child_count > 0:
        capacity_str = str(node.capacity) if node.capacity else '∞'
        line += f" [{node.child_count}/{capacity_str}]"

    # Add status symbol
    if options.show_status:
        status = node.effective_status
        symbol = SYMBOLS.get(status, '?')

        if options.use_color:
            color = COLORS.get(status, '')
            reset = COLORS['reset']
            line += f" {color}{symbol}{reset}"
        else:
            line += f" {symbol}"

    # Add description
    if options.verbose and node.description:
        desc = node.description[:60]
        if len(node.description) > 60:
            desc += '...'
        line += f" - {desc}"

    # Apply color to entire line
    if options.use_color and not options.show_status:
        status = node.effective_status
        color = COLORS.get(status, '')
        reset = COLORS['reset']
        line = f"{color}{line}{reset}"

    lines.append(line)

    # Render children
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)

        # Update prefix for children
        if node.depth == 0:
            child_prefix = ''
        else:
            extension = '    ' if is_last else '│   '
            child_prefix = prefix + extension

        child_lines = render_ascii(child, options, child_prefix, is_last_child)
        lines.extend(child_lines)

    return lines


def render_compact(node: TreeNode, options: RenderOptions, indent: int = 0) -> List[str]:
    """Render tree in compact format (simple indented list)."""
    lines = []

    # Build the node line
    line = '  ' * indent + f"{node.id}: {node.title}"

    lines.append(line)

    # Render children
    for child in node.children:
        child_lines = render_compact(child, options, indent + 1)
        lines.extend(child_lines)

    return lines


def render_markdown(node: TreeNode, options: RenderOptions, indent: int = 0) -> List[str]:
    """Render tree in markdown format."""
    lines = []

    # Build the node line
    prefix = '  ' * indent + '- '
    line = f"{prefix}**{node.id}: {node.title}**"

    # Add capacity
    if options.show_capacity and node.child_count > 0:
        capacity_str = str(node.capacity) if node.capacity else '∞'
        line += f" [{node.child_count}/{capacity_str}]"

    # Add status
    if options.show_status:
        status = node.effective_status
        line += f" `{status}`"

    lines.append(line)

    # Add description
    if options.verbose and node.description:
        desc_line = '  ' * (indent + 1) + node.description
        lines.append(desc_line)

    # Render children
    for child in node.children:
        child_lines = render_markdown(child, options, indent + 1)
        lines.extend(child_lines)

    return lines


def render(tree: TreeNode, options: RenderOptions) -> List[str]:
    """Render tree using the specified format."""
    if options.format == 'markdown':
        return render_markdown(tree, options)
    elif options.format == 'simple' or options.compact:
        return render_compact(tree, options)
    else:  # ascii
        return render_ascii(tree, options)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Display story tree as ASCII diagram',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --show-capacity --show-status
  %(prog)s --stage implemented --compact
  %(prog)s --root 2 --depth 2
  %(prog)s --format markdown > tree.md
        """
    )

    parser.add_argument('--root', default='root',
                        help='Start tree from specific node (default: root)')
    parser.add_argument('--depth', type=int, default=None,
                        help='Maximum depth to display (default: unlimited)')
    parser.add_argument('--stage', action='append', dest='stages',
                        help='Filter by stage (can specify multiple)')
    parser.add_argument('--exclude-stage', action='store_true',
                        help='Exclude specified stages instead of including')
    parser.add_argument('--compact', action='store_true',
                        help='Minimal output: ID and title only')
    parser.add_argument('--verbose', action='store_true',
                        help='Include description (truncated to 60 chars)')
    parser.add_argument('--show-capacity', action='store_true',
                        help='Show capacity as [children/capacity]')
    parser.add_argument('--show-status', action='store_true',
                        help='Show status indicator')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable ANSI color codes')
    parser.add_argument('--format', choices=['ascii', 'simple', 'markdown'],
                        default='ascii',
                        help='Output format (default: ascii)')
    parser.add_argument('--db', type=Path,
                        help='Custom database path')

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Resolve database path
    db_path = args.db or find_default_db()

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    # Query data
    rows = get_tree_data(
        db_path,
        args.root,
        args.depth,
        args.stages,
        args.exclude_stage
    )

    if not rows:
        print(f"No nodes found for root '{args.root}'")
        return 1

    # Build tree
    tree = build_tree(rows)

    if not tree:
        print("Failed to build tree")
        return 1

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

    return 0


if __name__ == '__main__':
    exit(main())
