#!/usr/bin/env python3
"""Run all code-sentinel checks on the codebase.

This script runs all available checks for recurring issues:
- Bash heredocs in GitHub Actions YAML
- grep -c exit code handling
- Git operations without staging
- Fixed window geometry
- PyInstaller hidden imports
"""

import sys
import subprocess
from pathlib import Path


def run_check(script_name, *args):
    """Run a check script and return results."""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + list(args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def main():
    print("🔍 Running Code-Sentinel checks...\n")

    checks_passed = 0
    checks_failed = 0

    # Get project root (assumes script is in .claude/skills/code-sentinel/scripts/)
    project_root = Path(__file__).parent.parent.parent.parent

    # Check 1: GitHub Actions YAML files for heredocs
    print("=" * 60)
    print("Checking GitHub Actions workflows for heredocs...")
    print("=" * 60)
    yaml_files = list(project_root.glob('.github/workflows/*.yml'))
    yaml_files.extend(list(project_root.glob('.github/workflows/*.yaml')))

    for yaml_file in yaml_files:
        returncode, stdout, stderr = run_check('check_heredoc_yaml.py', str(yaml_file))
        print(stdout)
        if returncode != 0:
            checks_failed += 1
        else:
            checks_passed += 1

    # Check 2: Shell scripts and YAML for grep exit codes
    print("\n" + "=" * 60)
    print("Checking for problematic grep -c patterns...")
    print("=" * 60)
    script_files = list(project_root.glob('**/*.sh'))
    script_files.extend(yaml_files)

    for script_file in script_files:
        if '.git' in str(script_file) or 'venv' in str(script_file):
            continue
        returncode, stdout, stderr = run_check('check_grep_exit_code.py', str(script_file))
        if 'Found' in stdout:  # Only print if issues found
            print(stdout)
            checks_failed += 1
        elif returncode == 0:
            checks_passed += 1

    # Check 3: YAML files for git operations
    print("\n" + "=" * 60)
    print("Checking for git operations without staging...")
    print("=" * 60)
    for yaml_file in yaml_files:
        returncode, stdout, stderr = run_check('check_git_operations.py', str(yaml_file))
        if 'Found' in stdout:
            print(stdout)
            checks_failed += 1
        elif returncode == 0:
            checks_passed += 1

    # Check 4: Python files for window geometry
    print("\n" + "=" * 60)
    print("Checking Python files for fixed window geometry...")
    print("=" * 60)
    py_files = list(project_root.glob('src/**/*.py'))

    for py_file in py_files:
        if '__pycache__' in str(py_file):
            continue
        returncode, stdout, stderr = run_check('check_window_geometry.py', str(py_file))
        if 'Found' in stdout:
            print(stdout)
            checks_failed += 1
        elif returncode == 0:
            checks_passed += 1

    # Check 5: PyInstaller spec for hidden imports
    print("\n" + "=" * 60)
    print("Checking PyInstaller spec for missing hidden imports...")
    print("=" * 60)
    spec_files = list(project_root.glob('*.spec'))

    for spec_file in spec_files:
        src_dir = project_root / 'src'
        if src_dir.exists():
            returncode, stdout, stderr = run_check(
                'check_pyinstaller_imports.py',
                str(spec_file),
                str(src_dir)
            )
            print(stdout)
            if returncode != 0:
                checks_failed += 1
            else:
                checks_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Checks passed: {checks_passed}")
    print(f"⚠️  Checks failed: {checks_failed}")

    if checks_failed > 0:
        print("\nSome checks found issues. Review the output above for details.")
        return 1
    else:
        print("\nAll checks passed! No recurring issues detected.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
