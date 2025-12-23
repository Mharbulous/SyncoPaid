#!/usr/bin/env python3
"""Check for fixed window geometry in Tkinter code.

Fixed geometry like .geometry("400x200") is fragile and doesn't adapt to content.
Use auto-sizing with minimum width instead.

Related commits: 216fce0
"""

import sys
import re
from pathlib import Path


def check_window_geometry(file_path):
    """Check for fixed window geometry in Python files."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Check for .geometry("WIDTHxHEIGHT") pattern
        match = re.search(r'\.geometry\s*\(\s*["\'](\d+)x(\d+)["\']', line)
        if match:
            width, height = match.groups()
            issues.append({
                'line': i,
                'content': line.strip(),
                'message': f'Fixed window geometry ({width}x{height}) may cut off content',
                'suggestion': 'Use auto-sizing: window.update_idletasks() then set minimum width',
                'commit': '216fce0'
            })

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_window_geometry.py <path-to-python-file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    if not file_path.suffix == '.py':
        print(f"⚠️  Warning: {file_path} is not a Python file")

    issues = check_window_geometry(file_path)

    if issues:
        print(f"⚠️  Found {len(issues)} window geometry issue(s) in {file_path}:\n")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['message']}")
            print(f"    Content: {issue['content']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print(f"    Related commit: {issue['commit']}\n")
        return 1
    else:
        print(f"✅ No window geometry issues found in {file_path}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
