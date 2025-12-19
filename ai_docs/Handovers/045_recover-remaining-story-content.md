# Handover: Recover Remaining Story Content from Git History

## Task
Recover missing `success_criteria` for node `8.4` from git history. The `root` node intentionally lacks story/criteria (it's the project root, not a user story).

## Current State
| Node | Title | Missing | Notes |
|------|-------|---------|-------|
| `root` | SyncoPaid | story + criteria | **Intentional** - project root |
| `8.4` | AI Disambiguation with Screenshot Context | success_criteria | **Epic node** - may have had criteria before |

Node `8.4` has a story populated and detailed Epic Overview in description, but `success_criteria` is NULL.

## Context

### What Happened
The three-field migration (`migrate_content_fields.py`) failed to parse inline comma-separated user stories. We created `restore_story_content.py` to fix 11 stories + 17 criteria, but `8.4` wasn't restored because its description uses a different format (`**Epic Overview:**` instead of standard user story).

### Key Files
- `.claude/data/story-tree.db` - SQLite database (closure table pattern)
- `dev-tools/xstory/migrate_content_fields.py` - Original migration (buggy regex)
- `dev-tools/xstory/restore_story_content.py` - Our fix script
- `.claude/data/plans/2025-12-19-story-tree-three-field-content-migration.md` - Migration plan

### Git Commits to Search
```bash
# Key migration commits
50a6d5f  chore(data): apply three-field content migration to story-tree.db
47cc1fb  feat(xstory): add migration plan and script for three-field content split
```

Search for commits touching `story-tree.db` before the migration:
```bash
git log --oneline --all -- .claude/data/story-tree.db | head -20
```

## Approach
1. Check git history for `story-tree.db` before commit `50a6d5f`
2. Extract node `8.4`'s `description` field from that version
3. If acceptance criteria existed, manually insert into `success_criteria` field
4. If `8.4` never had criteria (Epic nodes may not), document and close

## Branch
`claude/restore-story-nodes-Ut5a7` - continue work here
