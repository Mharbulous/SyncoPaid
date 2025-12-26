#!/usr/bin/env python3
"""Deterministic story prioritization script.

Generates a draft priority list based on complexity scoring and
dependency extraction. Designed to be called by the prioritize-story-nodes
skill, which then performs semantic analysis on the output.

Usage:
    python prioritize_stories.py [--output FILE] [--format markdown|json]
"""
import sqlite3
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = '.claude/data/story-tree.db'
OUTPUT_DIR = '.claude/data/priority-lists'

# Complexity indicators (higher = more complex)
COMPLEXITY_KEYWORDS = {
    'high': [
        'integration', 'api', 'database schema', 'migration', 'refactor',
        'architecture', 'security', 'authentication', 'performance',
        'real-time', 'async', 'concurrent', 'encryption', 'oauth',
        'webhook', 'background', 'queue', 'cache', 'index'
    ],
    'medium': [
        'validation', 'error handling', 'logging', 'configuration',
        'export', 'import', 'filter', 'search', 'sort', 'pagination'
    ],
    'low': [
        'add', 'display', 'show', 'simple', 'button', 'field', 'config',
        'setting', 'update', 'rename', 'label', 'text', 'tooltip', 'icon'
    ]
}

# Dependency patterns
DEPENDENCY_PATTERNS = [
    r'(?:requires|depends on|needs|after|blocked by|prerequisite[s]?[:\s]+)\s*(\d+(?:\.\d+)*)',
    r'(?:once|when|after)\s+(?:story\s+)?(\d+(?:\.\d+)*)\s+(?:is\s+)?(?:done|complete|implemented)',
    r'story\s+(\d+(?:\.\d+)*)\s+must\s+(?:be\s+)?(?:done|complete|implemented)\s+first',
]

# Prerequisite patterns (things this story needs that aren't other stories)
PREREQUISITE_PATTERNS = [
    r'(?:requires|needs|depends on)\s+([a-zA-Z][a-zA-Z0-9_\s]+?)(?:\s+(?:to be|is|are)|\.|,|$)',
    r'(?:after|once)\s+([a-zA-Z][a-zA-Z0-9_\s]+?)\s+(?:is|are)\s+(?:set up|configured|installed|available)',
]


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_dependencies(text):
    """Extract story ID dependencies from text."""
    if not text:
        return []

    dependencies = set()
    text_lower = text.lower()

    for pattern in DEPENDENCY_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        dependencies.update(matches)

    return sorted(dependencies)


def extract_prerequisites(text):
    """Extract non-story prerequisites from text."""
    if not text:
        return []

    prerequisites = set()

    for pattern in PREREQUISITE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up and filter out noise
            cleaned = match.strip().lower()
            if len(cleaned) > 3 and len(cleaned) < 50:
                # Skip if it looks like a story ID
                if not re.match(r'^\d+(\.\d+)*$', cleaned):
                    prerequisites.add(cleaned)

    return sorted(prerequisites)


def calculate_complexity(story):
    """Calculate complexity score for a story (0-100, lower = simpler)."""
    text = f"{story['title'] or ''} {story['description'] or ''} {story['success_criteria'] or ''}".lower()

    score = 50  # Base score

    # Keyword analysis
    high_count = sum(1 for kw in COMPLEXITY_KEYWORDS['high'] if kw in text)
    medium_count = sum(1 for kw in COMPLEXITY_KEYWORDS['medium'] if kw in text)
    low_count = sum(1 for kw in COMPLEXITY_KEYWORDS['low'] if kw in text)

    score += high_count * 10
    score += medium_count * 5
    score -= low_count * 5

    # Description length factor (longer = more complex)
    desc_len = len(story['description'] or '')
    if desc_len > 1000:
        score += 15
    elif desc_len > 500:
        score += 10
    elif desc_len > 200:
        score += 5
    elif desc_len < 100:
        score -= 5

    # Success criteria count (more criteria = more complex)
    criteria = story['success_criteria'] or ''
    criteria_count = len(re.findall(r'(?:^|\n)\s*[-*]', criteria))
    score += criteria_count * 3

    # Clamp to 0-100
    return max(0, min(100, score))


def get_eligible_stories():
    """Fetch stories eligible for prioritization."""
    conn = get_connection()

    # Eligible: not blocked, not on hold, no disposition
    # Include: approved, ready, planned stages (actionable)
    stories = conn.execute('''
        SELECT
            s.id,
            s.title,
            s.description,
            s.stage,
            s.hold_reason,
            s.disposition,
            s.notes,
            s.success_criteria,
            s.project_path,
            (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
            (SELECT GROUP_CONCAT(ancestor_id, ', ') FROM story_paths
             WHERE descendant_id = s.id AND depth > 0
             ORDER BY depth DESC) as ancestors
        FROM story_nodes s
        WHERE s.hold_reason IS NULL
          AND s.disposition IS NULL
          AND s.stage IN ('approved', 'ready', 'planned')
        ORDER BY s.stage, s.id
    ''').fetchall()

    conn.close()
    return [dict(row) for row in stories]


def generate_priority_list():
    """Generate the prioritized story list."""
    stories = get_eligible_stories()

    results = []
    for story in stories:
        combined_text = f"{story['description'] or ''}\n{story['notes'] or ''}"

        result = {
            'id': story['id'],
            'title': story['title'],
            'stage': story['stage'],
            'complexity': calculate_complexity(story),
            'prerequisites': extract_prerequisites(combined_text),
            'dependencies': extract_dependencies(combined_text),
            'node_depth': story['node_depth'] or 0,
            'ancestors': story['ancestors'],
            'project_path': story['project_path'],
        }
        results.append(result)

    # Sort by: stage priority, then complexity (ascending), then depth (descending)
    stage_order = {'ready': 0, 'planned': 1, 'approved': 2}
    results.sort(key=lambda x: (
        stage_order.get(x['stage'], 99),
        x['complexity'],
        -x['node_depth']
    ))

    return results


def format_markdown(results):
    """Format results as markdown."""
    lines = [
        f"# Draft Story Priority List",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Summary",
        f"",
        f"- Total eligible stories: {len(results)}",
        f"- By stage: " + ", ".join(
            f"{stage}: {sum(1 for r in results if r['stage'] == stage)}"
            for stage in ['ready', 'planned', 'approved']
            if any(r['stage'] == stage for r in results)
        ),
        f"",
        f"## Priority List",
        f"",
        f"| ID | Stage | Complexity | Prerequisites | Dependencies |",
        f"|:---|:------|:----------:|:--------------|:-------------|",
    ]

    for r in results:
        prereqs = ', '.join(r['prerequisites'][:3]) if r['prerequisites'] else '-'
        if len(r['prerequisites']) > 3:
            prereqs += f" (+{len(r['prerequisites'])-3} more)"

        deps = ', '.join(r['dependencies'][:3]) if r['dependencies'] else '-'
        if len(r['dependencies']) > 3:
            deps += f" (+{len(r['dependencies'])-3} more)"

        lines.append(f"| {r['id']} | {r['stage']} | {r['complexity']} | {prereqs} | {deps} |")

    lines.extend([
        f"",
        f"## Story Details",
        f"",
    ])

    for r in results:
        lines.extend([
            f"### {r['id']}: {r['title']}",
            f"",
            f"- **Stage**: {r['stage']}",
            f"- **Complexity Score**: {r['complexity']}",
            f"- **Node Depth**: {r['node_depth']}",
        ])

        if r['project_path']:
            lines.append(f"- **Project Path**: `{r['project_path']}`")

        if r['ancestors']:
            lines.append(f"- **Ancestors**: {r['ancestors']}")

        if r['prerequisites']:
            lines.append(f"- **Prerequisites**: {', '.join(r['prerequisites'])}")

        if r['dependencies']:
            lines.append(f"- **Dependencies (story IDs)**: {', '.join(r['dependencies'])}")

        lines.append(f"")

    return '\n'.join(lines)


def format_json(results):
    """Format results as JSON."""
    return json.dumps({
        'generated': datetime.now().isoformat(),
        'total_count': len(results),
        'stories': results
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Generate draft story priority list')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', '-f', choices=['markdown', 'json'],
                       default='markdown', help='Output format')
    args = parser.parse_args()

    results = generate_priority_list()

    if args.format == 'json':
        output = format_json(results)
        ext = '.json'
    else:
        output = format_markdown(results)
        ext = '.md'

    if args.output:
        output_path = Path(args.output)
    else:
        # Default output path
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_path = Path(OUTPUT_DIR) / f'priority-list-{timestamp}{ext}'

    output_path.write_text(output)
    print(f"Priority list written to: {output_path}")

    # Also print to stdout for immediate use
    print("\n" + "="*60 + "\n")
    print(output)


if __name__ == '__main__':
    main()
