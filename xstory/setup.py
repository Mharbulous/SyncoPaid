#!/usr/bin/env python3
"""
Xstory Setup Script

Installs xstory components into a target project directory.

Local development mode (default):
  - Creates symlinks for skills, commands, scripts (live updates)
  - Copies workflows and actions (GitHub requirement)

CI mode (--ci or CI=true environment):
  - Copies all files (no symlinks)

Usage:
  python setup.py install --target /path/to/project
  python setup.py install --target /path/to/project --ci
  python setup.py sync-workflows --target /path/to/project
  python setup.py init-db --target /path/to/project
"""

import argparse
import json
import os
import platform
import shutil
import sqlite3
import sys
from pathlib import Path


def is_ci_mode(force_ci: bool = False) -> bool:
    """Detect if running in CI environment."""
    if force_ci:
        return True
    if os.environ.get('CI', '').lower() == 'true':
        return True
    if platform.system() == 'Linux' and not os.environ.get('FORCE_SYMLINKS'):
        # Default to copy mode on Linux (common CI environment)
        # Set FORCE_SYMLINKS=1 to use symlinks on Linux
        return True
    return False


def get_xstory_root() -> Path:
    """Get the root directory of the xstory installation."""
    return Path(__file__).parent.resolve()


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def create_symlink(src: Path, dest: Path) -> None:
    """Create a symlink, removing existing file/link first."""
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    # On Windows, directory symlinks need special handling
    if platform.system() == 'Windows' and src.is_dir():
        os.symlink(src, dest, target_is_directory=True)
    else:
        os.symlink(src, dest)

    print(f"  Symlinked: {dest.name} -> {src}")


def copy_item(src: Path, dest: Path) -> None:
    """Copy a file or directory, removing existing first."""
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)

    print(f"  Copied: {dest.name}")


def install_skills(xstory_root: Path, target: Path, use_symlinks: bool) -> None:
    """Install skills to target/.claude/skills/"""
    src_dir = xstory_root / 'claude' / 'skills'
    dest_dir = target / '.claude' / 'skills'
    ensure_directory(dest_dir)

    print("\nInstalling skills...")
    for skill in src_dir.iterdir():
        if skill.is_dir():
            dest = dest_dir / skill.name
            if use_symlinks:
                create_symlink(skill, dest)
            else:
                copy_item(skill, dest)


def install_commands(xstory_root: Path, target: Path, use_symlinks: bool) -> None:
    """Install commands to target/.claude/commands/"""
    src_dir = xstory_root / 'claude' / 'commands'
    dest_dir = target / '.claude' / 'commands'
    ensure_directory(dest_dir)

    print("\nInstalling commands...")
    for cmd in src_dir.iterdir():
        if cmd.is_file() and cmd.suffix == '.md':
            dest = dest_dir / cmd.name
            if use_symlinks:
                create_symlink(cmd, dest)
            else:
                copy_item(cmd, dest)


def install_scripts(xstory_root: Path, target: Path, use_symlinks: bool) -> None:
    """Install scripts to target/.claude/scripts/"""
    src_dir = xstory_root / 'claude' / 'scripts'
    dest_dir = target / '.claude' / 'scripts'
    ensure_directory(dest_dir)

    print("\nInstalling scripts...")
    for script in src_dir.iterdir():
        if script.is_file() and script.suffix == '.py':
            dest = dest_dir / script.name
            if use_symlinks:
                create_symlink(script, dest)
            else:
                copy_item(script, dest)


def install_data_scripts(xstory_root: Path, target: Path, use_symlinks: bool) -> None:
    """Install data scripts to target/.claude/data/"""
    src_dir = xstory_root / 'claude' / 'data'
    dest_dir = target / '.claude' / 'data'
    ensure_directory(dest_dir)

    print("\nInstalling data scripts...")
    for script in src_dir.iterdir():
        if script.is_file() and script.suffix == '.py':
            dest = dest_dir / script.name
            if use_symlinks:
                create_symlink(script, dest)
            else:
                copy_item(script, dest)


def install_workflows(xstory_root: Path, target: Path) -> None:
    """Install workflows to target/.github/workflows/ (always copy, never symlink)"""
    src_dir = xstory_root / 'github' / 'workflows'
    dest_dir = target / '.github' / 'workflows'
    ensure_directory(dest_dir)

    print("\nInstalling workflows (always copied, GitHub requirement)...")
    for wf in src_dir.iterdir():
        if wf.is_file() and wf.suffix in ('.yml', '.yaml'):
            copy_item(wf, dest_dir / wf.name)


def install_actions(xstory_root: Path, target: Path) -> None:
    """Install GitHub Actions to target/.github/actions/ (always copy)"""
    src_dir = xstory_root / 'github' / 'actions'
    dest_dir = target / '.github' / 'actions'
    ensure_directory(dest_dir)

    print("\nInstalling GitHub Actions...")
    for action in src_dir.iterdir():
        if action.is_dir():
            copy_item(action, dest_dir / action.name)


def init_database(xstory_root: Path, target: Path) -> None:
    """Initialize an empty story-tree.db in the target project."""
    template = xstory_root / 'templates' / 'story-tree.db.empty'
    dest = target / '.claude' / 'data' / 'story-tree.db'

    ensure_directory(dest.parent)

    if dest.exists():
        print(f"\nDatabase already exists: {dest}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("Skipping database initialization.")
            return

    if template.exists():
        shutil.copy2(template, dest)
        print(f"\nInitialized database from template: {dest}")
    else:
        # Create empty database with schema
        schema_file = xstory_root / 'claude' / 'skills' / 'story-tree' / 'references' / 'schema.sql'
        if schema_file.exists():
            conn = sqlite3.connect(dest)
            with open(schema_file) as f:
                conn.executescript(f.read())
            conn.close()
            print(f"\nInitialized database from schema: {dest}")
        else:
            print(f"\nError: No template or schema found to initialize database")
            sys.exit(1)


def cmd_install(args) -> None:
    """Install xstory components to target project."""
    xstory_root = get_xstory_root()
    target = Path(args.target).resolve()
    use_symlinks = not is_ci_mode(args.ci)

    print(f"Xstory Installation")
    print(f"=" * 40)
    print(f"Source: {xstory_root}")
    print(f"Target: {target}")
    print(f"Mode: {'Copy (CI)' if not use_symlinks else 'Symlink (Local Dev)'}")

    if not target.exists():
        print(f"\nError: Target directory does not exist: {target}")
        sys.exit(1)

    install_skills(xstory_root, target, use_symlinks)
    install_commands(xstory_root, target, use_symlinks)
    install_scripts(xstory_root, target, use_symlinks)
    install_data_scripts(xstory_root, target, use_symlinks)
    install_workflows(xstory_root, target)
    install_actions(xstory_root, target)

    if args.init_db:
        init_database(xstory_root, target)

    print(f"\n{'=' * 40}")
    print("Installation complete!")

    if use_symlinks:
        print("\nSymlinks created. Changes to xstory will reflect immediately.")
    else:
        print("\nFiles copied. Run 'setup.py sync-workflows' after xstory updates.")


def cmd_sync_workflows(args) -> None:
    """Sync workflows from xstory to target (for after xstory updates)."""
    xstory_root = get_xstory_root()
    target = Path(args.target).resolve()

    print(f"Syncing workflows to {target}")
    install_workflows(xstory_root, target)
    install_actions(xstory_root, target)
    print("Workflow sync complete!")


def cmd_init_db(args) -> None:
    """Initialize story-tree.db in target project."""
    xstory_root = get_xstory_root()
    target = Path(args.target).resolve()
    init_database(xstory_root, target)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Xstory setup and installation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # install command
    install_parser = subparsers.add_parser('install', help='Install xstory to target project')
    install_parser.add_argument('--target', '-t', required=True, help='Target project directory')
    install_parser.add_argument('--ci', action='store_true', help='Force CI mode (copy instead of symlink)')
    install_parser.add_argument('--init-db', action='store_true', help='Initialize empty story-tree.db')
    install_parser.set_defaults(func=cmd_install)

    # sync-workflows command
    sync_parser = subparsers.add_parser('sync-workflows', help='Sync workflows to target (after xstory updates)')
    sync_parser.add_argument('--target', '-t', required=True, help='Target project directory')
    sync_parser.set_defaults(func=cmd_sync_workflows)

    # init-db command
    db_parser = subparsers.add_parser('init-db', help='Initialize story-tree.db in target project')
    db_parser.add_argument('--target', '-t', required=True, help='Target project directory')
    db_parser.set_defaults(func=cmd_init_db)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
