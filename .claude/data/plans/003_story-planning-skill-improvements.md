# Story Planning Skill Improvements - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the story-planning skill with bite-sized TDD tasks, explicit execution handoff, and complete code examples.

**Architecture:** Update the SKILL.md template to produce plans with granular steps following RED-GREEN-REFACTOR, exact commands with expected output, and execution options.

**Tech Stack:** Markdown skill file

---

## Summary of Improvements

The `superpowers:writing-plans` skill has several superior patterns that should be incorporated:

| Feature | Current story-planning | Improved (from writing-plans) |
|---------|------------------------|------------------------------|
| Task granularity | Multi-step tasks | Single-action steps (2-5 min each) |
| TDD enforcement | Optional testing plan | RED-GREEN-REFACTOR built into every task |
| Code examples | "Example code or pseudocode" | Complete, copy-paste ready code |
| Command output | "Run: command" | "Run: command" + "Expected: output" |
| Commit frequency | End of plan | After each task |
| Execution handoff | "say implement [id]" | Subagent-driven vs parallel session choice |
| Sub-skill reference | None | REQUIRED SUB-SKILL header |

---

## Task 1: Add Required Sub-Skill Header

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md:162-178`

**Step 1: Read current plan template header**

The current header starts at line 162:
```markdown
# [Story Title] - Implementation Plan

**Story ID:** [ID]
**Created:** [YYYY-MM-DD]
**Status:** planned
```

**Step 2: Replace with enhanced header**

```markdown
# [Story Title] - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** [ID]
**Created:** [YYYY-MM-DD]
**Status:** planned

**Goal:** [One sentence from story description]

**Architecture:** [2-3 sentences about implementation approach]

**Tech Stack:** [Key modules/libraries involved]

---
```

**Step 3: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): add required sub-skill header to plan template"
```

---

## Task 2: Replace Task Template with Bite-Sized Steps

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md:196-212`

**Step 1: Review current task template**

Current template:
```markdown
### Task 1: [First task title]

**Files:** `path/to/file.py`

[Detailed description of what to do]

```python
# Example code or pseudocode showing the approach
```

**Verification:** [How to verify this task is complete]
```

**Step 2: Replace with bite-sized TDD structure**

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    """Test that [behavior] works correctly."""
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL with "function not defined" or similar

**Step 3: Write minimal implementation**

```python
def function(input):
    """[Docstring]."""
    return expected
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

**Step 3: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): replace task template with bite-sized TDD steps"
```

---

## Task 3: Add Execution Handoff Section

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md:268-305` (Output Report section)

**Step 1: Read current next steps**

Current:
```markdown
## Next Steps

1. Review the implementation plan at `ai_docs/Plans/[filename]`
2. When ready to implement, say "implement [story-id]"
3. The story status is now `planned`
```

**Step 2: Replace with execution handoff options**

```markdown
## Execution Handoff

Plan complete and saved to `ai_docs/Plans/[filename]`.

**Two execution options:**

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Code review between tasks
- Fast iteration with quality gates
- **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development

**2. Parallel Session (separate)**
- Open new Claude Code session in this directory
- Batch execution with checkpoints
- **REQUIRED SUB-SKILL:** superpowers:executing-plans

**Which approach?**
```

**Step 3: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): add execution handoff with subagent/parallel options"
```

---

## Task 4: Add "Remember" Section with Key Principles

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md` (after Step 8, before Autonomous Operation)

**Step 1: Create new Remember section**

Add after the Output Report section (around line 305):

```markdown
## Remember

When generating plans, always:
- **Exact file paths** - never "somewhere in src/"
- **Complete code** - not "add validation" but the actual validation code
- **Exact commands with expected output** - not just "run tests"
- **DRY, YAGNI, TDD** - test first, minimal code, frequent commits
- **One action per step** - each step takes 2-5 minutes max
- **Reference relevant skills** - use @ syntax for skill references
```

**Step 2: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): add Remember section with key principles"
```

---

## Task 5: Update Quality Checks

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md:318-325`

**Step 1: Review current quality checks**

```markdown
## Quality Checks

Before completing the workflow, verify:
- [ ] All approved stories were fetched and analyzed
- [ ] Priority scoring was applied correctly
...
```

**Step 2: Add plan quality checks**

Add these items to the existing checklist:

```markdown
- [ ] Each task has exactly 5 steps: test, verify fail, implement, verify pass, commit
- [ ] All code examples are complete and copy-paste ready
- [ ] All commands include expected output
- [ ] No vague instructions like "add validation" or "handle errors"
- [ ] Execution handoff options are presented at end
```

**Step 3: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): add TDD quality checks for generated plans"
```

---

## Task 6: Update Common Mistakes Table

**Files:**
- Modify: `.claude/skills/story-planning/SKILL.md:327-336`

**Step 1: Review current common mistakes**

```markdown
| Mistake | What To Do Instead |
|---------|-------------------|
| Using `sqlite3` CLI | Use Python's sqlite3 module |
...
```

**Step 2: Add new common mistakes**

Add these rows:

```markdown
| Writing multi-step tasks | Break into single-action steps (test/verify/implement/verify/commit) |
| Omitting expected output | Every command needs "Expected: [what success looks like]" |
| Vague code examples | Write complete, copy-paste ready code |
| Skipping execution handoff | Always offer subagent-driven vs parallel session choice |
| Large commits at end | Commit after each task (RED-GREEN-REFACTOR cycle) |
```

**Step 3: Commit**

```bash
git add .claude/skills/story-planning/SKILL.md
git commit -m "feat(story-planning): add TDD-related common mistakes"
```

---

## Verification

After all tasks complete:

1. Read the updated SKILL.md and verify all sections are present
2. Manually trace through the workflow to ensure it produces bite-sized TDD plans
3. Verify the plan template includes all required elements:
   - Required sub-skill header
   - Goal/Architecture/Tech Stack
   - 5-step task structure (test, fail, implement, pass, commit)
   - Execution handoff options

---

## Rollback Plan

If changes cause issues with the story-planning workflow:

```bash
git log --oneline -10  # Find commit before changes
git revert <commit-hash>  # Revert specific change
# Or reset all changes:
git checkout HEAD~6 -- .claude/skills/story-planning/SKILL.md
```

---

## Notes

- The original story-planning skill is well-structured for selecting which story to plan
- These improvements focus on the **output format** of generated plans, not the selection logic
- The TDD enforcement aligns with superpowers:test-driven-development skill
- The execution handoff aligns with superpowers:executing-plans and superpowers:subagent-driven-development
