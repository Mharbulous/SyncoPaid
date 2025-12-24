# Xstory

Story-driven development orchestration tool for Claude Code.

## Overview

Xstory provides a complete workflow for managing development stories in Claude Code projects:

- **Story Tree**: Hierarchical story management with closure table pattern
- **CI/CD Integration**: GitHub Actions workflows for automated story processing
- **GUI Tool**: Visual story tree explorer and editor
- **Skills & Commands**: Claude Code integration for story operations

## Quick Start

### Installation

```bash
# Install to a project (creates symlinks for local dev)
python setup.py install --target /path/to/project

# Install with empty story database
python setup.py install --target /path/to/project --init-db

# CI mode (copies instead of symlinks)
python setup.py install --target /path/to/project --ci
```

### Syncing Workflows

After updating xstory, sync workflows to your projects:

```bash
python setup.py sync-workflows --target /path/to/project
```

## Directory Structure

```
xstory/
├── plugin.json              # Plugin manifest
├── setup.py                 # Installation script
├── README.md
├── gui/                     # Visual story explorer
│   ├── xstory.py           # Main PySide6 GUI
│   ├── build.py            # Build script
│   ├── requirements.txt
│   └── migrate_*.py        # Database migrations
├── claude/
│   ├── skills/             # Claude Code skills
│   │   ├── story-tree/     # Core tree operations
│   │   ├── story-planning/ # Story planning workflow
│   │   ├── story-execution/# Story execution
│   │   ├── story-building/ # Story building
│   │   ├── story-writing/  # Story writing
│   │   ├── story-vetting/  # Story vetting & dedup
│   │   ├── story-verification/
│   │   ├── story-arborist/ # Tree maintenance
│   │   ├── prioritize-story-nodes/
│   │   ├── code-sentinel/  # Code quality
│   │   └── goal-synthesis/ # Goal management
│   ├── commands/           # Slash commands
│   │   ├── plan-story.md
│   │   ├── write-story.md
│   │   ├── generate-stories.md
│   │   └── ci-*.md         # CI commands
│   ├── scripts/            # Helper scripts
│   │   ├── story_workflow.py
│   │   ├── prioritize_stories.py
│   │   └── story_tree_helpers.py
│   └── data/               # Data management scripts
│       ├── init_story_tree.py
│       └── insert_stories.py
├── github/
│   ├── workflows/          # GitHub Actions workflows
│   │   ├── story-tree-orchestrator.yml
│   │   ├── plan-stories.yml
│   │   ├── execute-stories.yml
│   │   ├── build-stories.yml
│   │   ├── review-stories.yml
│   │   ├── verify-stories.yml
│   │   └── activate-stories.yml
│   └── actions/            # Custom composite actions
│       ├── update-story-db/
│       └── post-story-results/
└── templates/
    └── story-tree.db.empty # Empty database template
```

## Deployment Modes

### Local Development (Symlinks)

Default on Windows. Changes to xstory reflect immediately in all linked projects.

```bash
python setup.py install --target ~/projects/MyApp
```

### CI Mode (Copies)

Default on Linux/CI. Files are copied (not symlinked) for reproducible builds.

```bash
python setup.py install --target /app --ci
```

To force symlinks on Linux:
```bash
FORCE_SYMLINKS=1 python setup.py install --target ~/projects/MyApp
```

## Database Schema

The story tree uses SQLite with a closure table pattern for efficient hierarchical queries.

Key tables:
- `story_nodes`: Story definitions with three-field workflow system
- `story_paths`: Closure table for ancestor/descendant relationships
- `story_commits`: Commit tracking per story
- `vetting_decisions`: Entity resolution cache

See `claude/skills/story-tree/references/schema.sql` for full schema.

## Workflow Stages

Stories progress through these stages:

```
concept → approved → planned → active → reviewing → verifying → implemented → ready → polish → released
```

Stories can be held (queued, pending, blocked, etc.) or disposed (rejected, archived, etc.) at any stage.

## License

MIT
