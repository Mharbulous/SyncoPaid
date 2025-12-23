#!/usr/bin/env python3
"""Check for git pull/rebase operations without staging/autostash.

Git operations can fail when there are uncommitted changes.
Always use git pull --rebase --autostash or stage files before pulling.

Related commits: 5dd2b28
"""

import sys
import re
from pathlib import Path


def check_git_operations(file_path):
    """Check for git operations that might fail with uncommitted changes."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Check for git pull/rebase without --autostash
        if re.search(r'git\s+(pull|rebase)', line):
            if '--autostash' not in line:
                # Check if there's a git add before this (within 3 lines)
                has_git_add = False
                for j in range(max(0, i - 4), i):
                    if j < len(lines) and 'git add' in lines[j]:
                        has_git_add = True
                        break

                if not has_git_add:
                    issues.append({
                        'line': i,
                        'content': line.strip(),
                        'message': 'git pull/rebase without --autostash or preceding git add',
                        'suggestion': 'Use git pull --rebase --autostash or stage files first with git add',
                        'commit': '5dd2b28'
                    })

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_git_operations.py <path-to-file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    issues = check_git_operations(file_path)

    if issues:
        print(f"⚠️  Found {len(issues)} git operation issue(s) in {file_path}:\n")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['message']}")
            print(f"    Content: {issue['content']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print(f"    Related commit: {issue['commit']}\n")
        return 1
    else:
        print(f"✅ No git operation issues found in {file_path}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
