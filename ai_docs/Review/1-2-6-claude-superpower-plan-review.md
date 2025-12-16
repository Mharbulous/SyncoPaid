# Plan Review: Screenshot Retention & Cleanup Policy

**Plan File:** `ai_docs\Plans\1-2-6-screenshot-retention-cleanup.md`
**Reviewed Against:** `superpowers:writing-plans` skill
**Review Date:** 2025-12-16
**Overall Grade:** B- (Good content, needs structural reformatting)

---

## 1. Header Evaluation

| Requirement | Status | Notes |
|-------------|--------|-------|
| Feature name heading | ✅ Pass | Has `# Screenshot Retention & Cleanup Policy` |
| Required sub-skill reference | ❌ **Missing** | Must add: `> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans...` |
| **Goal:** one sentence | ⚠️ Partial | Has goal but different format |
| **Architecture:** 2-3 sentences | ⚠️ Partial | Called "Approach" - should be "Architecture" |
| **Tech Stack:** | ✅ Pass | Present |
| `---` separator | ✅ Pass | Present |

---

## 2. Task Structure Evaluation

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Files:** section with exact paths | ⚠️ Partial | Uses `\|` pipe format instead of bullet list |
| Create/Modify/Test labels | ❌ Missing | Should specify Create/Modify/Test for each file |
| Complete code in plan | ✅ Pass | Full code provided |
| Exact commands | ✅ Pass | `pytest` commands with expected output |
| Line numbers for modifications | ⚠️ Partial | Only in "Files Affected" table, not in tasks |

---

## 3. Bite-Sized Step Granularity Evaluation

### Current Format (RED/GREEN/COMMIT)

```
RED: Write test + expected failure
GREEN: Write code + expected pass
COMMIT: Commit
```

### Required Format (5 Explicit Steps)

```
Step 1: Write the failing test
Step 2: Run test to verify it fails
Step 3: Write minimal implementation
Step 4: Run test to verify it passes
Step 5: Commit
```

### Issues

| Issue | Impact |
|-------|--------|
| RED combines "write test" + "run test" | Not atomic - engineer may skip verification |
| GREEN combines "write code" + "run test" | Not atomic - engineer may skip verification |
| Missing explicit "run" steps | No clear checkpoint to verify RED/GREEN |

---

## 4. Strengths

- ✅ Complete code examples for all tasks
- ✅ Good acceptance criteria with checkmarks
- ✅ Edge cases documented
- ✅ Verification section present
- ✅ Proper TDD flow (test first, then implement)
- ✅ Commit commands included
- ✅ Story context and prerequisites documented
- ✅ Files Affected summary table

---

## 5. Required Changes

### 5.1 Add Required Sub-Skill Header

Add immediately after the main heading:

```markdown
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
```

### 5.2 Rename "Approach" to "Architecture"

Change:
```markdown
**Approach:** Create an `ArchiveWorker` class...
```

To:
```markdown
**Architecture:** Create an `ArchiveWorker` class...
```

### 5.3 Restructure Tasks from RED/GREEN to 5 Explicit Steps

Each task should follow this structure:

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

[code block]

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "specific error message"

**Step 3: Write minimal implementation**

[code block]

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: description"
```
```

### 5.4 Change Files Format

Change from pipe separator:
```markdown
**Files:** Test: `tests/test_archiver.py` | Impl: `src/syncopaid/archiver.py`
```

To bullet list with labels:
```markdown
**Files:**
- Create: `tests/test_archiver.py`
- Create: `src/syncopaid/archiver.py`
```

---

## 6. Recommendation

The plan content is solid and follows good TDD principles. The main issues are structural formatting that doesn't match the `superpowers:writing-plans` skill template.

**Action:** Reformat the plan to match the skill structure exactly, which will make it compatible with `superpowers:executing-plans` for automated task-by-task implementation.
