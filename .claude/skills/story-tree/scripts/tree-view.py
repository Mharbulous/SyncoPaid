#!/usr/bin/env python3
"""
Story Tree ASCII Visualizer

Usage: python tree-view.py [--db PATH] [--root ID] [--depth N] [--status S] [--format ascii|markdown]
"""

import argparse
import io
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STATUS_SYMBOLS_UNICODE = {
    'infeasible': '∅', 'rejected': '✗', 'wishlist': '?',
    'concept': '·', 'queued': '⏳', 'pending': '❓', 'approved': '✓',
    'blocked': '⊗', 'planned': '○', 'broken': '⚠', 'paused': '⏸',
    'active': '●', 'conflict': '⚡',
    'reviewing': '👁', 'implemented': '★',
    'ready': '✔', 'polish': '◇', 'released': '🚀',
    'legacy': '◊', 'deprecated': '⊘', 'archived': '📦',
}

STATUS_SYMBOLS_ASCII = {
    'infeasible': '0', 'rejected': 'x', 'wishlist': 'W',
    'concept': '.', 'queued': 'Q', 'pending': '?', 'approved': 'v',
    'blocked': 'X', 'planned': 'o', 'broken': '!', 'paused': '|',
    'active': 'O', 'conflict': 'C',
    'reviewing': 'R', 'implemented': '+',
    'ready': '#', 'polish': 'p', 'released': '^',
    'legacy': 'L', 'deprecated': '-', 'archived': 'A',
}

ANSI_COLORS = {
    'infeasible': '\033[38;2;139;0;0m', 'rejected': '\033[38;2;255;69;0m',
    'wishlist': '\033[38;2;255;140;0m', 'concept': '\033[38;2;255;165;0m',
    'queued': '\033[38;2;255;200;0m', 'pending': '\033[38;2;255;215;0m',
    'approved': '\033[38;2;255;219;88m', 'blocked': '\033[38;2;184;134;11m',
    'planned': '\033[38;2;238;232;170m', 'broken': '\033[38;2;218;165;32m',
    'paused': '\033[38;2;189;183;107m', 'active': '\033[38;2;50;205;50m',
    'conflict': '\033[38;2;255;99;71m',
    'reviewing': '\033[38;2;64;224;208m', 'implemented': '\033[38;2;65;105;225m',
    'ready': '\033[38;2;0;0;255m', 'polish': '\033[38;2;0;71;171m',
    'released': '\033[38;2;65;105;225m', 'legacy': '\033[38;2;75;0;130m',
    'deprecated': '\033[38;2;148;0;211m', 'archived': '\033[38;2;128;0;128m',
    'reset': '\033[0m',
}

BOX_UNICODE = {'branch': '├── ', 'last_branch': '└── ', 'vertical': '│   ', 'empty': '    '}
BOX_ASCII = {'branch': '+-- ', 'last_branch': '\\-- ', 'vertical': '|   ', 'empty': '    '}


def can_use_unicode() -> bool:
    if sys.platform == 'win32':
        if not sys.stdout.isatty():
            return True
        try:
            '●'.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, LookupError):
            return False
    return True


@dataclass
class TreeNode:
    id: str
    title: str
    status: str
    capacity: int
    child_count: int
    depth: int
    description: str = ''
    children: list = field(default_factory=list)


@dataclass
class RenderOptions:
    compact: bool = False
    verbose: bool = False
    show_capacity: bool = False
    show_status: bool = True
    show_status_label: bool = False
    show_ids: bool = True
    use_color: bool = True
    force_ascii: bool = False
    format: str = 'ascii'


def find_default_db() -> Path:
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path
    cwd = Path.cwd()
    db_path = cwd / '.claude' / 'data' / 'story-tree.db'
    if db_path.exists():
        return db_path
    if sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            db_path = Path(local_app_data) / 'story-tree' / 'story-tree.db'
            if db_path.exists():
                return db_path
    raise FileNotFoundError("Could not find story-tree.db. Use --db to specify the path.")


def get_tree_data(db_path: Path, root_id: str = 'root', max_depth: Optional[int] = None,
                  statuses: Optional[list[str]] = None, exclude_statuses: bool = False) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT s.id, s.title, s.description,
            COALESCE(s.disposition, s.hold_reason, s.stage) AS status,
            s.capacity, st.depth,
            (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
            (SELECT st2.ancestor_id FROM story_paths st2 WHERE st2.descendant_id = s.id AND st2.depth = 1) as parent_id
        FROM story_nodes s
        JOIN story_paths st ON s.id = st.descendant_id
        WHERE st.ancestor_id = :root_id
    """
    params = {'root_id': root_id}

    if max_depth is not None:
        query += " AND st.depth <= :max_depth"
        params['max_depth'] = max_depth

    if statuses:
        placeholders = ', '.join(f':status_{i}' for i in range(len(statuses)))
        query += f" AND COALESCE(s.disposition, s.hold_reason, s.stage) {'NOT ' if exclude_statuses else ''}IN ({placeholders})"
        for i, status in enumerate(statuses):
            params[f'status_{i}'] = status

    query += " ORDER BY st.depth, s.id"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def build_tree(rows: list[dict]) -> tuple[Optional[TreeNode], list[TreeNode]]:
    if not rows:
        return None, []

    nodes = {}
    for row in rows:
        nodes[row['id']] = TreeNode(
            id=row['id'], title=row['title'], status=row['status'],
            capacity=row['capacity'], child_count=row['child_count'],
            depth=row['depth'], description=row['description'] or '',
        )

    root = None
    orphans = []
    for row in rows:
        node = nodes[row['id']]
        parent_id = row['parent_id']
        if row['depth'] == 0:
            root = node
        elif parent_id and parent_id in nodes:
            nodes[parent_id].children.append(node)
        else:
            orphans.append(node)

    return root, orphans


def colorize(text: str, status: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI_COLORS.get(status, '')}{text}{ANSI_COLORS['reset']}"


def render_node_label(node: TreeNode, options: RenderOptions) -> str:
    if options.compact:
        return f"{node.id}: {node.title}"

    parts = []
    if options.show_ids and node.id != 'root':
        parts.append(f"({node.id})")
    parts.append(node.title)
    if options.show_capacity:
        parts.append(f"[{node.child_count}/{node.capacity}]")
    if options.show_status:
        symbols = STATUS_SYMBOLS_ASCII if options.force_ascii or not can_use_unicode() else STATUS_SYMBOLS_UNICODE
        symbol = colorize(symbols.get(node.status, '?'), node.status, options.use_color)
        parts.append(symbol)
        if options.show_status_label:
            parts.append(f"({node.status})")
    if options.verbose and node.description:
        parts.append(f"- {node.description[:60]}{'...' if len(node.description) > 60 else ''}")
    return ' '.join(parts)


def render_ascii(node: TreeNode, options: RenderOptions, prefix: str = '') -> list[str]:
    box = BOX_ASCII if options.force_ascii or not can_use_unicode() else BOX_UNICODE
    lines = [prefix + render_node_label(node, options)]

    for i, child in enumerate(node.children):
        is_last = (i == len(node.children) - 1)
        connector = box['last_branch'] if is_last else box['branch']
        child_prefix = prefix + (box['empty'] if is_last else box['vertical'])

        lines.append(prefix + connector + render_node_label(child, options))
        if child.children:
            lines.extend(render_children(child.children, options, child_prefix, box))
    return lines


def render_children(children: list, options: RenderOptions, prefix: str, box: dict) -> list[str]:
    lines = []
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        connector = box['last_branch'] if is_last else box['branch']
        lines.append(prefix + connector + render_node_label(child, options))
        child_prefix = prefix + (box['empty'] if is_last else box['vertical'])
        if child.children:
            lines.extend(render_children(child.children, options, child_prefix, box))
    return lines


def render_markdown(node: TreeNode, options: RenderOptions, indent: int = 0) -> list[str]:
    parts = []
    if node.depth == 0:
        parts.append(f"**{node.title}**")
    elif node.child_count > 0:
        parts.append(f"**{node.id} {node.title}**")
    else:
        parts.append(f"{node.id} {node.title}")
    if options.show_capacity:
        parts.append(f"[{node.child_count}/{node.capacity}]")
    if options.show_status:
        parts.append(f"`{node.status}`")

    lines = ['  ' * indent + f"- {' '.join(parts)}"]
    for child in node.children:
        lines.extend(render_markdown(child, options, indent + 1))
    return lines


def render(node: TreeNode, options: RenderOptions) -> list[str]:
    if options.format == 'markdown':
        return render_markdown(node, options)
    return render_ascii(node, options)


def main():
    parser = argparse.ArgumentParser(description='Display story tree as ASCII diagram')
    parser.add_argument('--root', default='root', help='Start from node ID')
    parser.add_argument('--depth', type=int, help='Maximum depth')
    parser.add_argument('--status', action='append', dest='statuses', help='Filter by status')
    parser.add_argument('--exclude-status', action='store_true', help='Exclude statuses')
    parser.add_argument('--compact', action='store_true', help='Minimal output')
    parser.add_argument('--verbose', action='store_true', help='Include description')
    parser.add_argument('--show-capacity', action='store_true', help='Show [children/capacity]')
    parser.add_argument('--hide-status', action='store_true', help='Hide status symbols')
    parser.add_argument('--show-status', action='store_true', help='Show status name')
    parser.add_argument('--no-color', action='store_true', help='Disable colors')
    parser.add_argument('--hide-ids', action='store_true', help='Hide node IDs')
    parser.add_argument('--force-ascii', action='store_true', help='ASCII only')
    parser.add_argument('--format', choices=['ascii', 'markdown'], default='ascii')
    parser.add_argument('--db', type=Path, help='Database path')
    args = parser.parse_args()

    try:
        db_path = args.db if args.db else find_default_db()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    try:
        rows = get_tree_data(db_path, args.root, args.depth, args.statuses, args.exclude_status)
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print(f"No nodes found for root '{args.root}'", file=sys.stderr)
        sys.exit(1)

    tree, orphans = build_tree(rows)

    if not tree and orphans:
        print(f"# Filtered results ({len(orphans)} nodes):")
        symbols = STATUS_SYMBOLS_ASCII if args.force_ascii else STATUS_SYMBOLS_UNICODE
        for node in orphans:
            print(f"{node.id}: {node.title} {symbols.get(node.status, '?')}")
        sys.exit(0)

    if not tree:
        print("Error: Could not build tree", file=sys.stderr)
        sys.exit(1)

    options = RenderOptions(
        compact=args.compact, verbose=args.verbose, show_capacity=args.show_capacity,
        show_status=not args.hide_status, show_status_label=args.show_status,
        show_ids=not args.hide_ids, use_color=not args.no_color and sys.stdout.isatty(),
        force_ascii=args.force_ascii, format=args.format,
    )
    print('\n'.join(render(tree, options)))


if __name__ == '__main__':
    main()
