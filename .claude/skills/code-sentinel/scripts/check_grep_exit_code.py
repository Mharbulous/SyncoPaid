#!/usr/bin/env python3
"""Check for problematic grep -c || echo "0" pattern.

grep -c returns exit code 1 when count is 0, causing || echo to execute
and create duplicate output. Use || true instead.

Related commits: 4115ba9
"""

import sys
import re
from pathlib import Path


def check_grep_exit_code(file_path):
    """Check for grep -c || echo "0" pattern."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Check for grep -c followed by || echo
        if re.search(r'grep\s+-c.*\|\|\s*echo\s+["\']0["\']', line):
            issues.append({
                'line': i,
                'content': line.strip(),
                'message': 'grep -c with || echo "0" creates double output when count is 0',
                'suggestion': 'Use || true instead: grep -c pattern file || true',
                'commit': '4115ba9'
            })

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_grep_exit_code.py <path-to-file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    issues = check_grep_exit_code(file_path)

    if issues:
        print(f"⚠️  Found {len(issues)} grep exit code issue(s) in {file_path}:\n")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['message']}")
            print(f"    Content: {issue['content']}")
            print(f"    Suggestion: {issue['suggestion']}")
            print(f"    Related commit: {issue['commit']}\n")
        return 1
    else:
        print(f"✅ No grep exit code issues found in {file_path}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
