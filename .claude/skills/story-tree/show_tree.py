#!/usr/bin/env python3
"""Display the current story tree structure."""

import sqlite3
from pathlib import Path
from collections import defaultdict

def get_tree_stats(conn):
    """Get overall tree statistics."""
    cursor = conn.cursor()

    # Status counts
    cursor.execute('SELECT status, COUNT(*) FROM stories GROUP BY status ORDER BY status')
    status_counts = dict(cursor.fetchall())

    # Total nodes
    cursor.execute('SELECT COUNT(*) FROM stories')
    total_nodes = cursor.fetchone()[0]

    # Depth distribution (depth from root)
    cursor.execute('''
        SELECT
            COALESCE((SELECT depth FROM story_tree WHERE ancestor_id = 'root' AND descendant_id = s.id), 0) as node_depth,
            COUNT(*) as count
        FROM stories s
        GROUP BY node_depth
        ORDER BY node_depth
    ''')
    depth_counts = dict(cursor.fetchall())

    # Capacity analysis
    cursor.execute('''
        SELECT
            s.id,
            s.story,
            s.capacity,
            (SELECT COUNT(*) FROM story_tree WHERE ancestor_id = s.id AND depth = 1) as child_count,
            COALESCE((SELECT depth FROM story_tree WHERE ancestor_id = 'root' AND descendant_id = s.id), 0) as node_depth
        FROM stories s
        WHERE s.status != 'deprecated'
        ORDER BY node_depth, s.id
    ''')
    capacity_data = cursor.fetchall()

    return {
        'total_nodes': total_nodes,
        'status_counts': status_counts,
        'depth_counts': depth_counts,
        'capacity_data': capacity_data
    }

def build_tree_structure(conn):
    """Build tree structure for visualization."""
    cursor = conn.cursor()

    # Get all stories with their relationships
    cursor.execute('''
        SELECT
            s.id,
            s.story,
            s.status,
            s.capacity,
            (SELECT COUNT(*) FROM story_tree WHERE ancestor_id = s.id AND depth = 1) as child_count,
            COALESCE((SELECT depth FROM story_tree WHERE ancestor_id = 'root' AND descendant_id = s.id), 0) as node_depth
        FROM stories s
        ORDER BY s.id
    ''')
    stories_data = {row[0]: {
        'id': row[0],
        'story': row[1],
        'status': row[2],
        'capacity': row[3],
        'child_count': row[4],
        'depth': row[5]
    } for row in cursor.fetchall()}

    # Get parent-child relationships
    cursor.execute('''
        SELECT ancestor_id, descendant_id
        FROM story_tree
        WHERE depth = 1
        ORDER BY descendant_id
    ''')
    children_by_parent = defaultdict(list)
    for parent_id, child_id in cursor.fetchall():
        children_by_parent[parent_id].append(child_id)

    return stories_data, children_by_parent

def print_tree_node(story_id, stories, children_by_parent, prefix='', is_last=True):
    """Recursively print tree node with ASCII art."""
    story = stories[story_id]

    # Determine connector
    connector = '└── ' if is_last else '├── '

    # Format status indicator
    status_indicator = {
        'implemented': '✓',
        'in-progress': '▶',
        'planned': '○',
        'concept': '·',
        'active': '★',
        'deprecated': '✗'
    }.get(story['status'], '?')

    # Format capacity info
    capacity_info = f"[{story['child_count']}/{story['capacity']}]"

    # Print current node
    print(f"{prefix}{connector}{status_indicator} {story['id']}: {story['story']} {capacity_info}")

    # Print children
    children = children_by_parent.get(story_id, [])
    for i, child_id in enumerate(children):
        is_last_child = (i == len(children) - 1)
        extension = '    ' if is_last else '│   '
        print_tree_node(child_id, stories, children_by_parent,
                       prefix + extension, is_last_child)

def display_tree(db_path):
    """Display the current story tree."""
    conn = sqlite3.connect(db_path)

    # Get statistics
    stats = get_tree_stats(conn)

    # Print header
    print("=" * 80)
    print("STORY TREE - Current Status")
    print("=" * 80)
    print()

    # Print overall metrics
    print("📊 Overall Metrics")
    print("-" * 80)
    print(f"Total nodes: {stats['total_nodes']}")
    print()

    # Print status breakdown
    print("Status breakdown:")
    for status, count in sorted(stats['status_counts'].items()):
        percentage = (count / stats['total_nodes'] * 100) if stats['total_nodes'] > 0 else 0
        print(f"  {status:15s}: {count:3d} ({percentage:5.1f}%)")
    print()

    # Print depth distribution
    print("Depth distribution:")
    for depth, count in sorted(stats['depth_counts'].items()):
        print(f"  Level {depth}: {count:3d} nodes")
    print()

    # Print capacity analysis
    print("📈 Capacity Analysis (by level)")
    print("-" * 80)
    level_capacity = defaultdict(lambda: {'total_capacity': 0, 'total_children': 0, 'nodes': []})
    for node_id, story, capacity, child_count, depth in stats['capacity_data']:
        level_capacity[depth]['total_capacity'] += capacity
        level_capacity[depth]['total_children'] += child_count
        if child_count < capacity:
            level_capacity[depth]['nodes'].append((node_id, story, child_count, capacity))

    for depth in sorted(level_capacity.keys()):
        data = level_capacity[depth]
        fill_rate = (data['total_children'] / data['total_capacity'] * 100) if data['total_capacity'] > 0 else 0
        print(f"Level {depth}: {data['total_children']}/{data['total_capacity']} ({fill_rate:.1f}% full)")

        # Show under-capacity nodes
        under_capacity = data['nodes']
        if under_capacity:
            print(f"  Under-capacity nodes:")
            for node_id, story, child_count, capacity in under_capacity:
                print(f"    {node_id}: {story[:50]:50s} [{child_count}/{capacity}]")
    print()

    # Print tree structure
    print("🌳 Tree Structure")
    print("-" * 80)
    print("Legend: ★=active ✓=implemented ▶=in-progress ○=planned ·=concept ✗=deprecated")
    print()

    # Build and display tree
    stories, children_by_parent = build_tree_structure(conn)
    print_tree_node('root', stories, children_by_parent, prefix='', is_last=True)

    print()
    print("=" * 80)

    # Get metadata
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM metadata ORDER BY key')
    metadata = dict(cursor.fetchall())

    if metadata:
        print()
        print("📝 Metadata")
        print("-" * 80)
        for key, value in sorted(metadata.items()):
            print(f"  {key}: {value}")

    conn.close()

if __name__ == '__main__':
    db_path = Path(__file__).parent.parent.parent / 'data/story-tree.db'
    display_tree(db_path)
