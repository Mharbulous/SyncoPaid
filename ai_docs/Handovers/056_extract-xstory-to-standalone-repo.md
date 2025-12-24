# Handover: Extract Xstory into Standalone Repository

## Objective

Extract Xstory dev tool components from SyncoPaid into a standalone git repo that can be shared across multiple projects via symlinks (local dev) and submodules/copies (CI).

## Context

User has TWO apps (SyncoPaid + another) and wants to:
1. Actively develop Xstory while working on both apps
2. Have Xstory changes instantly reflect in both apps during local dev
3. Maintain reproducible CI builds

## Target Architecture

```
~/projects/
├── xstory/                    # NEW: Standalone repo
│   ├── plugin.json
│   ├── gui/
│   │   ├── xstory.py
│   │   ├── build.py
│   │   └── requirements.txt
│   ├── claude/
│   │   ├── skills/            # All story-* skills
│   │   ├── commands/          # Story-related commands
│   │   └── scripts/           # story_*.py helpers
│   ├── github/
│   │   └── workflows/         # *-stories.yml workflows
│   ├── templates/
│   │   └── story-tree.db.empty
│   └── setup.py               # Installs symlinks or copies
│
├── SyncoPaid/                 # App A
│   ├── .claude/skills/story-* → symlinks to xstory
│   └── .github/workflows/*-stories.yml  # COPIES (GitHub requirement)
│
└── OtherApp/                  # App B (same pattern)
```

## Components to Extract

### From `.claude/skills/` (10 skills)
- story-tree, story-planning, story-execution, story-building
- story-writing, story-vetting, story-verification, story-arborist
- prioritize-story-nodes, code-sentinel

### From `.claude/commands/` (8 commands)
- plan-story.md, generate-stories.md, write-story.md, review-stories.md
- vet-stories.md, ci-identify-plan.md, ci-decompose-plan.md, ci-execute-plan.md

### From `.claude/scripts/` (5 scripts)
- story_workflow.py, story_tree_helpers.py, prioritize_stories.py
- insert_story.py, generate_vision_doc.py

### From `.github/workflows/` (8 workflows)
- story-tree-orchestrator.yml, plan-stories.yml, execute-stories.yml
- build-stories.yml, review-stories.yml, verify-stories.yml
- activate-stories.yml, synthesize-goals-non-goals.yml

### From `dev-tools/xstory/` (GUI - already isolated)
- xstory.py, build.py, migrations, requirements.txt

## Key Implementation Details

### setup.py Behavior

```python
# Detect environment
if os.environ.get('CI') or platform.system() == 'Linux':
    # CI mode: copy files
    copy_tree(src, dest)
else:
    # Local mode: create symlinks
    os.symlink(src, dest)
```

### GitHub Workflows Caveat

GitHub Actions requires workflows to be real files in `.github/workflows/`. Options:
1. **Copy on setup** - setup.py copies workflows (needs manual sync)
2. **Sync script** - `xstory sync-workflows` command to update
3. **Git hook** - Auto-sync on xstory commits

Recommend option 2 with reminder in README.

### Plugin Format (Future Marketplace Compatibility)

```json
// plugin.json
{
  "name": "xstory",
  "version": "1.0.0",
  "description": "Story-driven development orchestration",
  "skills": ["story-tree", "story-planning", ...],
  "commands": ["plan-story", ...]
}
```

## Key Files in Current Repo

| Path | Purpose |
|------|---------|
| `dev-tools/xstory/xstory.py` | GUI application (already isolated) |
| `.claude/skills/story-tree/SKILL.md` | Core skill - closure table pattern |
| `.claude/skills/story-tree/references/schema.sql` | Database schema |
| `.claude/scripts/story_workflow.py` | Consolidated DB query helper |
| `.github/workflows/story-tree-orchestrator.yml` | Main CI loop |

## Irrelevant Files (Red Herrings)

- `.claude/archived-skills/` - Deprecated, don't migrate
- `.claude/skills/streamline/` - Not story-related, leave in app
- `.claude/skills/user-manual-generator/` - App-specific, leave in app
- `.claude/skills/session-start-hook/` - Personal skill, not xstory

## Technical References

### Agent Skills Standard
- https://agentskills.io - Open standard adopted by OpenAI, Microsoft, Cursor
- https://github.com/anthropics/skills - Official reference (Apache 2.0)

### Claude Code Plugin System
- Plugin marketplace in public beta (Oct 2025)
- Plugins bundle skills + commands + MCP servers
- `marketplace.json` enables discovery on claudecodemarketplace.com

### Community Resources
- https://skillsmp.com - 25k+ skills marketplace
- https://github.com/jeremylongshore/claude-code-plugins-plus-skills - 243 plugins

## Implementation Steps

### Phase 1: Create Xstory Repo Structure
1. Create `~/projects/xstory/` with directory structure
2. Move GUI files from `dev-tools/xstory/` → `xstory/gui/`
3. Copy (not move yet) skills/commands/scripts → `xstory/claude/`
4. Copy workflows → `xstory/github/workflows/`
5. Create `plugin.json` with metadata

### Phase 2: Build setup.py
1. Argument parsing: `setup.py install [--target PATH] [--ci]`
2. Symlink creation for `.claude/skills/`, `.claude/commands/`, `.claude/scripts/`
3. File copy for `.github/workflows/` (always copy, never symlink)
4. Empty story-tree.db initialization
5. CI detection and copy-mode fallback

### Phase 3: Test in SyncoPaid
1. Remove original files from SyncoPaid
2. Run `setup.py install --target ~/projects/SyncoPaid`
3. Verify skills/commands work
4. Verify CI workflows run
5. Verify Xstory GUI launches

### Phase 4: Deploy to Second App
1. Run `setup.py install --target ~/projects/OtherApp`
2. Initialize story-tree.db for that project
3. Verify cross-project workflow

## Success Criteria

- [ ] Xstory repo contains all components in clean structure
- [ ] `setup.py install` works on Windows and Linux
- [ ] Symlinks work for local development
- [ ] CI workflows execute successfully
- [ ] Changes to xstory/ reflect in both apps without manual sync
- [ ] GUI launches from either app context
