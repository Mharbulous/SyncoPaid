# Handover: Create StoryTree GitHub Repository

## Naming Convention

- **StoryTree**: The repository name and overall project for story-driven development orchestration
- **Xstory** (eXploreStory): The Python GUI tool (PySide6) within StoryTree for visually exploring and managing the story tree

## Task

Create standalone GitHub repo `Mharbulous/StoryTree` and push the extracted story-tree components.

## Status: ✅ COMPLETE

## What Was Done

1. ✅ GitHub repo created: https://github.com/Mharbulous/StoryTree (private)
2. ✅ Local folder initialized: `C:\Users\Brahm\Git\StoryTree`
3. ✅ Content copied from `SyncoPaid/xstory/`
4. ✅ Initial commit pushed (96 files, 19,117 lines)

### Repository Structure

```
StoryTree/
├── setup.py             # Tested installer (symlinks/copies)
├── README.md
├── gui/                 # Xstory (eXploreStory): PySide6 GUI tool
├── claude/
│   ├── skills/          # 11 skills (story-*, code-sentinel, goal-synthesis)
│   ├── commands/        # 11 slash commands
│   ├── scripts/         # 5 helper scripts
│   └── data/            # DB init scripts
├── github/
│   ├── workflows/       # 8 CI workflows
│   └── actions/         # 2 composite actions
└── templates/
    └── story-tree.db.empty  # Empty v4.0 schema DB
```

## Optional Next Steps

- Add GitHub topics: `claude-code`, `story-driven-development`, `developer-tools`
- Make repo public when ready
- Test installation back into SyncoPaid:
  ```bash
  cd C:\Users\Brahm\Git\StoryTree
  python setup.py install --target C:\Users\Brahm\Git\SyncoPaid --init-db
  ```

## Reference

| Resource | Location |
|----------|----------|
| StoryTree repo | https://github.com/Mharbulous/StoryTree |
| Local folder | `C:\Users\Brahm\Git\StoryTree` |
| Original extraction plan | `ai_docs/Handovers/056_extract-xstory-to-standalone-repo.md` |
