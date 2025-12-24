# Handover: Create Xstory GitHub Repository

## Task

Create standalone GitHub repo `Mharbulous/xstory` and push the extracted xstory directory.

## What's Done

The `xstory/` directory in SyncoPaid contains all extracted components, committed and pushed to branch `claude/extract-xstory-repo-QX2FM`:

```
xstory/
├── plugin.json          # Claude Code marketplace manifest
├── setup.py             # Tested installer (symlinks/copies)
├── README.md
├── gui/                 # PySide6 story explorer (from dev-tools/xstory/)
├── claude/
│   ├── skills/          # 11 skills (story-*, code-sentinel, goal-synthesis)
│   ├── commands/        # 10 slash commands
│   ├── scripts/         # 5 helper scripts
│   └── data/            # DB init scripts
├── github/
│   ├── workflows/       # 8 CI workflows
│   └── actions/         # 2 composite actions
└── templates/
    └── story-tree.db.empty  # Empty v4.0 schema DB
```

## What's Needed

1. Create GitHub repo: `gh repo create Mharbulous/xstory --public --description "Story-driven development orchestration for Claude Code"`

2. Initialize and push:
```bash
cd ~/projects
mkdir xstory && cd xstory
git init -b main
cp -r ~/projects/SyncoPaid/xstory/* .
git add .
git commit -m "Initial commit: xstory standalone plugin"
git remote add origin git@github.com:Mharbulous/xstory.git
git push -u origin main
```

3. Optional: Add GitHub topics: `claude-code`, `story-driven-development`, `developer-tools`

## Key Files

| File | Purpose |
|------|---------|
| `xstory/setup.py` | Installer - already tested, works |
| `xstory/plugin.json` | Plugin manifest |
| `ai_docs/Handovers/056_extract-xstory-to-standalone-repo.md` | Original extraction plan |

## Blockers

Sandbox environment cannot create new git repos (commit signing tied to SyncoPaid). Must run in local VS Code terminal.

## After Repo Creation

Once `Mharbulous/xstory` exists, test installation back into SyncoPaid:

```bash
# From xstory repo
python setup.py install --target ~/projects/SyncoPaid --init-db
```

This validates the full round-trip: extract → standalone repo → reinstall via symlinks.
