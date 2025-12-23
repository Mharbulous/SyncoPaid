#!/usr/bin/env python3
"""Check for missing hidden imports in PyInstaller spec after refactoring.

When code is refactored into new modules, hidden imports must be explicitly
listed in the PyInstaller spec file.

Related commits: 68be291
"""

import sys
import re
from pathlib import Path


def get_spec_hidden_imports(spec_path):
    """Extract hidden imports from PyInstaller spec file."""
    hidden_imports = set()

    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find hiddenimports list
    match = re.search(r'hiddenimports\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if match:
        imports_str = match.group(1)
        # Extract quoted strings
        for imp in re.findall(r'["\']([^"\']+)["\']', imports_str):
            hidden_imports.add(imp)

    return hidden_imports


def get_python_imports(py_path):
    """Extract imports from Python source file."""
    imports = set()

    with open(py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        # Match: from package.module import ...
        match = re.match(r'from\s+([\w.]+)\s+import', line)
        if match:
            imports.add(match.group(1))

        # Match: import package.module
        match = re.match(r'import\s+([\w.]+)', line)
        if match:
            imports.add(match.group(1))

    return imports


def check_pyinstaller_imports(spec_path, src_dir):
    """Check for imports that might be missing from PyInstaller spec."""
    issues = []

    if not spec_path.exists():
        return [{'message': f'PyInstaller spec file not found: {spec_path}'}]

    hidden_imports = get_spec_hidden_imports(spec_path)

    # Check Python files in src directory
    for py_file in Path(src_dir).rglob('*.py'):
        # Skip __pycache__ and tests
        if '__pycache__' in str(py_file) or 'test' in str(py_file):
            continue

        file_imports = get_python_imports(py_file)

        # Check for syncopaid imports not in hidden imports
        for imp in file_imports:
            if imp.startswith('syncopaid.') and imp not in hidden_imports:
                # Only flag if this is a deeper module (likely refactored)
                if imp.count('.') >= 2:
                    issues.append({
                        'file': str(py_file),
                        'import': imp,
                        'message': f'Module {imp} may need to be added to hiddenimports',
                        'suggestion': f'Add "{imp}" to hiddenimports list in {spec_path.name}',
                        'commit': '68be291'
                    })

    return issues


def main():
    if len(sys.argv) < 3:
        print("Usage: python check_pyinstaller_imports.py <path-to-spec> <src-directory>")
        sys.exit(1)

    spec_path = Path(sys.argv[1])
    src_dir = Path(sys.argv[2])

    if not src_dir.exists():
        print(f"Error: Source directory not found: {src_dir}")
        sys.exit(1)

    issues = check_pyinstaller_imports(spec_path, src_dir)

    # Remove duplicates
    unique_issues = []
    seen = set()
    for issue in issues:
        key = issue.get('import', issue.get('message'))
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    if unique_issues:
        print(f"⚠️  Found {len(unique_issues)} potential PyInstaller import issue(s):\n")
        for issue in unique_issues:
            if 'import' in issue:
                print(f"  {issue['message']}")
                print(f"    Found in: {issue['file']}")
                print(f"    Suggestion: {issue['suggestion']}")
                print(f"    Related commit: {issue['commit']}\n")
            else:
                print(f"  {issue['message']}\n")
        return 1
    else:
        print(f"✅ No PyInstaller import issues found")
        return 0


if __name__ == '__main__':
    sys.exit(main())
