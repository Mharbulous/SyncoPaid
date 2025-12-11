# Story Tree Skill

Build out ideas for apps and features in a structured way using story trees.

## Workflow Decision Logic

Before brainstorming new ideas, this skill must first ensure the current app's existing user stories are adequately mapped. Follow this decision flow:

### Phase 1: Story Tree Status Check

**First, check if a story tree already exists:**

1. Look for `STORY_TREE.md` in the project root or `ai_docs/` directory
2. If found, proceed to **Phase 2: Coverage Validation**
3. If not found, proceed to **Phase 3: Map Existing Stories**

### Phase 2: Coverage Validation

**Determine if the existing story tree adequately describes the current app:**

Validation checklist:
- [ ] All modules in the codebase have corresponding user stories
- [ ] PRD user stories (if exists) are reflected in the story tree
- [ ] Recent features (check git commits, handovers) are documented
- [ ] Story tree structure matches actual app capabilities
- [ ] No orphan features exist (implemented but undocumented)

**Scoring:**
- 5/5 checks pass: Story tree is **COMPLETE** - proceed to Phase 4 (Brainstorming)
- 3-4 checks pass: Story tree is **PARTIAL** - update missing stories, then brainstorm
- 0-2 checks pass: Story tree is **OUTDATED** - return to Phase 3

### Phase 3: Map Existing Stories

**Document what the app currently does before ideating new features:**

1. **Analyze the codebase:**
   - Read CLAUDE.md, README, and PRD documents
   - List all modules and their purposes
   - Identify user-facing features vs internal utilities

2. **Extract user stories from:**
   - PRD documents (explicit user stories)
   - Module docstrings and comments
   - Tray/UI menu items (implies user actions)
   - Config options (implies user preferences)
   - Export/import capabilities (implies data workflows)

3. **Create the story tree structure** using the template below

4. **Validate completeness** (return to Phase 2)

### Phase 4: Brainstorm New Ideas

**Only after the story tree is validated as COMPLETE or PARTIAL:**

1. **Review the existing story tree** for gaps and opportunities
2. **Identify enhancement areas:**
   - Existing stories that could be extended
   - Adjacent features users might need
   - Quality-of-life improvements
   - Integration opportunities

3. **Add new stories with status: IDEA**
4. **Prioritize** using MoSCoW or value/effort matrix

---

## Story Tree Template

Use this template when creating `STORY_TREE.md`:

```markdown
# [App Name] Story Tree

## Meta
- **Current State:** UNMAPPED | PARTIAL | MAPPED | COMPLETE
- **Last Validated:** YYYY-MM-DD
- **Coverage:** X/Y features documented

---

## Epic: Core Functionality

### Story: [Descriptive Title]
**As a** [user type], **I want** [capability] **so that** [value]

**Status:** IMPLEMENTED
**Module:** `module.py` (lines X-Y)
**Config:** `setting_name` (optional)

#### Acceptance Criteria:
- [x] Criterion met in implementation
- [x] Another criterion

---

## Ideas Backlog

### Idea: [Future Feature]
**As a** [user], **I want** [feature] **so that** [benefit]

**Priority:** HIGH | MEDIUM | LOW
**Complexity:** S | M | L | XL
**Dependencies:** [list or "none"]
```

---

## Commands

When user invokes this skill, follow this interaction pattern:

### `/story-tree status`
Check current story tree status and report coverage.

### `/story-tree map`
Analyze codebase and create/update the story tree for existing features.

### `/story-tree validate`
Run coverage validation checklist and report gaps.

### `/story-tree brainstorm [area]`
Generate new feature ideas (only if status >= PARTIAL).

### `/story-tree add [story]`
Add a new story or idea to the tree.

---

## Auto-Detection Triggers

Automatically engage story tree workflow when user asks:
- "What features should we add?"
- "Let's brainstorm new ideas"
- "What's next for this app?"
- "I want to extend the app"
- "Plan new features"

**Before brainstorming, always verify story tree status first.**

---

## Example Session Flow

**Scenario: User wants to brainstorm but no story tree exists**

```
User: Let's brainstorm some new features for the app

Claude: I'd be happy to brainstorm new features! However, I notice this project
       doesn't have a story tree yet. Before we generate new ideas, let me first
       map out the existing features so we can build on them effectively.

       [Analyzes codebase, creates STORY_TREE.md with existing features]

Claude: I've created a story tree documenting the current app capabilities:
       - 8 implemented user stories across 3 epics
       - Coverage: 8/8 modules documented
       - Status: MAPPED

       Now we can brainstorm! Based on the existing features, here are some ideas...
```

**Scenario: Story tree exists but is outdated**

```
User: What new features should we add?

Claude: Let me check the current story tree status...

       Found STORY_TREE.md but it appears outdated:
       - 2 new modules added since last validation
       - Recent git commits show screenshot feature not documented
       - Coverage: 6/8 modules (PARTIAL)

       Before brainstorming, let me update the story tree with these new features.

       [Updates STORY_TREE.md]

Claude: Story tree is now current. Ready to brainstorm new ideas!
```

**Scenario: Story tree is complete**

```
User: I want to extend the app with some new capabilities

Claude: Let me check the story tree status...

       STORY_TREE.md validated:
       - All 8 modules have corresponding stories
       - PRD stories are reflected
       - Recent features documented
       - Coverage: COMPLETE

       Great! Here are enhancement opportunities based on the existing stories:

       1. [Idea] Extended export formats (builds on Export epic)
       2. [Idea] Notification system (extends UI epic)
       3. [Idea] Data backup/restore (enhances Data Management)

       Which area interests you most?
```
