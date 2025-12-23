"""
Tests for recurring code patterns that have caused bugs.

These tests detect patterns that have caused issues in the past.
When tests fail, use the code-sentinel skill to fix them automatically.

Based on analysis of 185 commits - see:
ai_docs/Reports/2025-12-22-Recurring-Fixes.md
"""

import re
from pathlib import Path
import pytest


class TestCIWorkflowPatterns:
    """Test CI/CD workflow patterns (78% of recurring fixes)"""

    def test_no_heredocs_in_github_actions(self):
        """Prevent bash heredocs in GitHub Actions YAML files.

        Issue: Heredocs fail with indentation inside YAML run: blocks
        Fix: Use string concatenation instead
        Related commit: d1394da
        """
        workflow_dir = Path('.github/workflows')
        if not workflow_dir.exists():
            pytest.skip("No GitHub workflows directory")

        issues = []
        for yaml_file in workflow_dir.glob('*.yml'):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            in_run_block = False
            for i, line in enumerate(lines, 1):
                if re.search(r'^\s+run:\s*\|', line):
                    in_run_block = True
                elif in_run_block and re.match(r'^\s{0,6}\w', line):
                    in_run_block = False

                if in_run_block and re.search(r'<<["\']?EOF["\']?', line):
                    issues.append(f"{yaml_file}:{i} - {line.strip()}")

        assert not issues, (
            "Bash heredocs detected in GitHub Actions YAML (commit d1394da):\n" +
            "\n".join(issues) +
            '\n\nFix: Use string concatenation: VAR="line1"\nVAR="${VAR}\\nline2"'
        )

    def test_no_grep_exit_code_echo_pattern(self):
        """Prevent grep -c || echo "0" pattern.

        Issue: grep -c returns exit code 1 when count is 0, causing || echo
               to execute and create duplicate output
        Fix: Use || true instead
        Related commit: 4115ba9
        """
        issues = []

        # Check shell scripts
        for script_file in Path('.').rglob('*.sh'):
            if '.git' in str(script_file) or 'venv' in str(script_file):
                continue

            with open(script_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if re.search(r'grep\s+-c.*\|\|\s*echo\s+["\']0["\']', line):
                    issues.append(f"{script_file}:{i} - {line.strip()}")

        # Check YAML workflows
        workflow_dir = Path('.github/workflows')
        if workflow_dir.exists():
            for yaml_file in workflow_dir.glob('*.yml'):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if re.search(r'grep\s+-c.*\|\|\s*echo\s+["\']0["\']', line):
                        issues.append(f"{yaml_file}:{i} - {line.strip()}")

        assert not issues, (
            "grep -c with || echo '0' creates double output (commit 4115ba9):\n" +
            "\n".join(issues) +
            "\n\nFix: Use || true instead: grep -c pattern file || true"
        )

    def test_git_operations_with_staging(self):
        """Ensure git pull/rebase operations handle uncommitted changes.

        Issue: Git operations fail when there are uncommitted changes
        Fix: Use --autostash or stage files before pulling
        Related commit: 5dd2b28
        """
        workflow_dir = Path('.github/workflows')
        if not workflow_dir.exists():
            pytest.skip("No GitHub workflows directory")

        issues = []
        for yaml_file in workflow_dir.glob('*.yml'):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if re.search(r'git\s+(pull|rebase)', line):
                    if '--autostash' not in line:
                        # Check if there's a git add within 3 lines before
                        has_git_add = False
                        for j in range(max(0, i - 4), i):
                            if 'git add' in lines[j - 1]:
                                has_git_add = True
                                break

                        if not has_git_add:
                            issues.append(f"{yaml_file}:{i} - {line.strip()}")

        assert not issues, (
            "git pull/rebase without --autostash or git add (commit 5dd2b28):\n" +
            "\n".join(issues) +
            "\n\nFix: Use git pull --rebase --autostash or stage files first"
        )


class TestApplicationPatterns:
    """Test application code patterns (22% of recurring fixes)"""

    def test_no_fixed_window_geometry(self):
        """Prevent fixed window geometry in Tkinter code.

        Issue: Fixed geometry like .geometry("400x200") cuts off content
        Fix: Use auto-sizing with update_idletasks() and set minimum width
        Related commit: 216fce0
        """
        issues = []

        src_dir = Path('src')
        if not src_dir.exists():
            pytest.skip("No src directory")

        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                match = re.search(r'\.geometry\s*\(\s*["\'](\d+)x(\d+)["\']', line)
                if match:
                    width, height = match.groups()
                    issues.append(f"{py_file}:{i} - {line.strip()} [size: {width}x{height}]")

        assert not issues, (
            "Fixed window geometry found (commit 216fce0):\n" +
            "\n".join(issues) +
            "\n\nFix: Use auto-sizing:\n" +
            "  window.update_idletasks()\n" +
            "  window.minsize(WIDTH, 0)  # minimum width only"
        )

    def test_pyinstaller_hidden_imports(self):
        """Check that refactored modules are in PyInstaller hidden imports.

        Issue: Refactored modules need explicit listing in hiddenimports
        Fix: Add module paths to hiddenimports list in .spec file
        Related commit: 68be291
        """
        spec_files = list(Path('.').glob('*.spec'))
        if not spec_files:
            pytest.skip("No PyInstaller spec files")

        src_dir = Path('src')
        if not src_dir.exists():
            pytest.skip("No src directory")

        # Get all hidden imports from spec files
        hidden_imports = set()
        for spec_file in spec_files:
            with open(spec_file, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'hiddenimports\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if match:
                imports_str = match.group(1)
                for imp in re.findall(r'["\']([^"\']+)["\']', imports_str):
                    hidden_imports.add(imp)

        # Find deeply nested syncopaid imports (likely from refactoring)
        issues = []
        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or 'test' in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find syncopaid imports
            for match in re.finditer(r'from\s+(syncopaid\.[\w.]+)\s+import', content):
                module = match.group(1)
                # Check deeply nested modules (2+ dots = likely refactored)
                if module.count('.') >= 2 and module not in hidden_imports:
                    issues.append(f"{module} (used in {py_file})")

        # Remove duplicates
        issues = sorted(set(issues))

        assert not issues, (
            "Modules may need to be added to PyInstaller hiddenimports (commit 68be291):\n" +
            "\n".join(issues) +
            f"\n\nFix: Add to hiddenimports list in {spec_files[0].name}"
        )

    def test_sibling_imports_use_relative_syntax(self):
        """Ensure sibling module imports use relative syntax.

        Issue: Absolute imports for sibling modules fail in PyInstaller bundles
               because the module is not at the top level namespace
        Fix: Use relative imports (from .module import ...) for sibling modules
        Related commit: 2024964
        """
        src_dir = Path('src/syncopaid')
        if not src_dir.exists():
            pytest.skip("No src/syncopaid directory")

        # Get all syncopaid module names (without .py extension)
        syncopaid_modules = set()
        for py_file in src_dir.glob('*.py'):
            if py_file.stem != '__init__':
                syncopaid_modules.add(py_file.stem)

        issues = []
        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # Match: from module_name import ... (absolute import)
                # But NOT: from .module_name import ... (relative import)
                # And NOT: from syncopaid.module import ... (qualified import)
                match = re.match(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', line)
                if match:
                    module_name = match.group(1)
                    # Check if this is a sibling syncopaid module
                    if module_name in syncopaid_modules:
                        issues.append(
                            f"{py_file}:{i} - from {module_name} import ...\n"
                            f"  Fix: from .{module_name} import ..."
                        )

        assert not issues, (
            "Absolute imports for sibling modules fail in PyInstaller (commit 2024964):\n" +
            "\n".join(issues) +
            "\n\nFix: Use relative imports: from .module import ..."
        )


class TestCodeQualityPatterns:
    """Test general code quality patterns"""

    def test_deterministic_file_sorting(self):
        """Ensure file selection uses deterministic sorting.

        Issue: Non-deterministic sorting leads to unpredictable behavior
        Fix: Always include filename as secondary sort key
        Related commits: dc6d1af, 71e8761
        """
        issues = []

        # Look for sorted() calls without secondary sort key
        for py_file in Path('.').rglob('*.py'):
            if '.git' in str(py_file) or 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find sorted() with key parameter
            for match in re.finditer(r'sorted\([^)]*key\s*=\s*lambda[^:]+:\s*([^,\)]+)', content):
                key_expr = match.group(1).strip()
                # Check if it's not a tuple (single value sort)
                if not key_expr.startswith('('):
                    # This might be non-deterministic
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(
                        f"{py_file}:{line_num} - sorted with single key: {key_expr}\n"
                        f"  Consider: key=lambda x: ({key_expr}, x.name)"
                    )

        # This is a warning, not a hard failure (too many false positives)
        if issues:
            pytest.skip(
                "Potential non-deterministic sorting (commits dc6d1af, 71e8761):\n" +
                "\n".join(issues[:5]) +  # Limit to first 5
                "\n\nNote: Add filename as secondary sort key if selection order matters"
            )
