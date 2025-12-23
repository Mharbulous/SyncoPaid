#!/usr/bin/env python3
"""Check for bash heredocs in GitHub Actions YAML files.

Heredocs fail with indentation inside YAML run: blocks.
Suggest using string concatenation instead.

Related commits: d1394da
"""

import sys
import re
from pathlib import Path


def check_heredoc_yaml(file_path):
    """Check for heredoc syntax in YAML workflow files."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_run_block = False
    for i, line in enumerate(lines, 1):
        # Detect if we're in a run: block
        if re.search(r'^\s+run:\s*\|', line):
            in_run_block = True
        elif in_run_block and re.match(r'^\s{0,6}\w', line):
            # Exit run block when indentation returns to YAML level
            in_run_block = False

        # Check for heredoc syntax in run blocks
        if in_run_block and re.search(r'<<["\']?EOF["\']?', line):
            issues.append({
                'line': i,
                'content': line.strip(),
                'message': 'Bash heredoc detected in YAML run block',
                'suggestion': 'Use string concatenation instead: VAR="value1"\nVAR="${VAR}value2"',
                'commit': 'd1394da'
            })

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_heredoc_yaml.py <path-to-yaml-file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    issues = check_heredoc_yaml(file_path)

    if issues:
        print(f"⚠️  Found {len(issues)} heredoc issue(s) in {file_path}:\n")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['message']}")
            print(f"    Content: {issue['content']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print(f"    Related commit: {issue['commit']}\n")
        return 1
    else:
        print(f"✅ No heredoc issues found in {file_path}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
