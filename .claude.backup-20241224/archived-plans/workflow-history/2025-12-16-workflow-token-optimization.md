# Workflow Token Optimization Plan

## Analysis Summary

**Analyzed Run:** daily-plan-story.yml (2025-12-16)
**Total Cost:** $0.7665
**Duration:** 346.2 seconds
**Output Plan Size:** 1,339 lines / 42,833 characters (~10,700 tokens)

### Token Breakdown by Phase

| Phase | Input Tokens | Notes |
|-------|-------------|-------|
| System Initialization | 20,174 | Base context + tools |
| SlashCommand (/plan-story) | +621 | 51-line command prompt |
| Skill (story-planning) | +4,000 | 482-line SKILL.md |
| Database Queries | ~500 | Multiple Python -c calls |
| File Reads | ~3,000 | technical-reference.md, tracker.py, database.py, config.py |
| Plan Output | ~11,935 | Very verbose TDD template |

**Estimated Savings Potential:** 40-60% reduction (~$0.30-0.45 per run)

---

## Inefficiencies Identified

### 1. Skill Prompt Bloat (High Impact)

**Problem:** The story-planning SKILL.md is 482 lines designed for interactive use, but CI mode only needs core workflow steps.

**Wasted Sections:**
- "When to Use" / "When NOT to Use" (~30 lines) - Claude already invoked via slash command
- Full interactive handoff template (Step 8) (~60 lines) - CI cannot respond
- "Quality Standards" table (~15 lines) - redundant with template
- "Common Mistakes to Avoid" table (~15 lines) - training data, not runtime needed
- "Pre-Completion Checklist" (~15 lines) - interactive reminders

**Estimated Waste:** ~135 lines / ~1,000 tokens per run

### 2. Verbose Plan Template (High Impact)

**Problem:** Each TDD task generates 3 full checkpoint sections with:
- Complete code examples (often 30-50 lines each)
- Verbose markdown formatting
- Redundant verification commands

**Current:** 7 tasks × ~170 lines = ~1,190 lines of TDD content
**Optimal:** 7 tasks × ~60 lines = ~420 lines

**Estimated Waste:** ~770 lines / ~6,000 tokens per run

### 3. Redundant Prompt Layering (Medium Impact)

**Problem:** Three layers of instructions all loaded:
1. Workflow prompt (daily-plan-story.yml) - 97 lines
2. Slash command (plan-story.md) - 51 lines
3. Skill prompt (SKILL.md) - 482 lines

Many instructions overlap (git operations, autonomous mode, constraints).

**Estimated Waste:** ~50 lines / ~400 tokens per run

### 4. Full File Reads (Medium Impact)

**Problem:** Read entire files when only specific sections needed:
- `tracker.py` - 400+ lines, only needed lines ~88-120, ~204-256
- `database.py` - 300+ lines, only needed schema section
- `config.py` - 150+ lines, only needed DEFAULT_CONFIG dict

**Estimated Waste:** ~500 lines / ~4,000 tokens per run

### 5. JSON Parsing Workaround (Low Impact)

**Problem:** Embedded JSON in bash command failed, requiring:
1. Failed parsing attempt (wasted tokens)
2. Write to /tmp/stories.json (extra step)
3. Re-read and process (duplicate work)

**Root Cause:** Special characters in story descriptions (backticks, newlines)

**Estimated Waste:** ~200 tokens per failure

### 6. No Early Exit Check (Low Impact)

**Problem:** Full skill prompt loads before checking if approved stories exist. If no approved stories, entire skill context was wasted.

**Estimated Waste:** ~4,000 tokens when no stories available

---

## Refactoring Recommendations

### Recommendation 1: Create CI-Optimized Skill Mode

**Priority:** High
**Estimated Savings:** ~1,000 tokens per run

**Approach:** Add a CI mode flag to the skill that omits interactive sections.

**Option A: Conditional Sections in SKILL.md**

```markdown
## Step 8: Output Report

<!-- CI_MODE_START: Skip to minimal output -->
**When running in CI/automation context**, use minimal output:
```
✓ Planned story [STORY_ID]: [Title]
  Plan: ai_docs/Plans/[filename].md
```
<!-- CI_MODE_END -->

<!-- INTERACTIVE_MODE_START: Include full handoff -->
[Full interactive handoff content here]
<!-- INTERACTIVE_MODE_END -->
```

**Option B: Separate SKILL-CI.md File**

Create `.claude/skills/story-planning/SKILL-CI.md` with:
- Core workflow steps only (Steps 1-7)
- Minimal output format (Step 8 CI)
- No "When to Use", "Common Mistakes", "Quality Standards"
- ~200 lines instead of 482

**Option C: Workflow-Embedded Prompt**

Move essential skill instructions into the workflow prompt itself, eliminating skill invocation overhead.

**Recommended:** Option B (separate CI file) - cleanest separation, no conditional parsing

### Recommendation 2: Compact Plan Template

**Priority:** High
**Estimated Savings:** ~6,000 tokens per run

**Approach:** Create a compact TDD template for CI-generated plans.

**Current Format (per task):**
```markdown
### Task 1: [Name]

**Objective:** [description]

**Files:**
- Test: `path`
- Implementation: `path`

---

**⚠️ TDD CHECKPOINT 1: RED - Write Failing Test**

Create test that specifies the expected behavior:

```python
[30-50 lines of example code]
```

**Verify RED:**
```bash
[command]
```
**Expected output:** [description]

---

**⚠️ TDD CHECKPOINT 2: GREEN - Minimal Implementation**

[30-50 more lines]

---

**⚠️ TDD CHECKPOINT 3: COMMIT**

[10 lines]
```

**Compact Format (per task):**
```markdown
### Task 1: [Name]

**Files:** Test: `path` | Impl: `path`

**RED:** Create test for [behavior]. Run: `pytest path::test_name -v` → Expect: FAILED

**GREEN:** Implement [minimal solution]. Run: `pytest path::test_name -v` → Expect: PASSED

**COMMIT:** `git add [files] && git commit -m "feat: [message]"`
```

**Benefits:**
- Same information density
- 60% fewer tokens
- Implementer still knows exactly what to do
- Code examples generated at implementation time, not planning time

### Recommendation 3: Consolidate Prompt Layers

**Priority:** Medium
**Estimated Savings:** ~400 tokens per run

**Approach:** Merge redundant instructions between workflow, slash command, and skill.

**Current Flow:**
```
Workflow Prompt → SlashCommand → Skill
     ↓                ↓            ↓
  Git ops         Invoke skill    Full workflow
  YOLO mode       Arg parsing     All steps
  Constraints     Constraints     Report format
```

**Optimized Flow:**
```
Workflow Prompt (CI-specific) → Skill-CI
         ↓                          ↓
  All CI instructions          Core workflow only
  Git ops, YOLO, constraints   Steps 1-7 + minimal output
```

**Changes:**
1. Remove slash command layer for CI (invoke skill directly)
2. Move CI-specific instructions to workflow prompt
3. Remove redundant "constraints" sections from skill

### Recommendation 4: Targeted File Reading

**Priority:** Medium
**Estimated Savings:** ~4,000 tokens per run

**Approach:** Read only needed file sections using line ranges.

**Current:**
```python
Read(file_path="src/syncopaid/tracker.py")  # 400+ lines
```

**Optimized:**
```python
Read(file_path="src/syncopaid/tracker.py", offset=88, limit=40)  # ActivityEvent only
Read(file_path="src/syncopaid/tracker.py", offset=204, limit=60)  # TrackerLoop.__init__ only
```

**Implementation:**
- Pre-define key section locations in technical-reference.md
- Update skill to use offset/limit parameters
- Create a "code landmarks" reference file for common read targets

### Recommendation 5: Fix JSON Handling

**Priority:** Low
**Estimated Savings:** ~200 tokens when triggered

**Approach:** Avoid embedding JSON in bash commands.

**Current (fails on special chars):**
```python
python -c "
stories_data = '''[{\"description\": \"...\"}]'''
stories = json.loads(stories_data)
"
```

**Fixed (use separate query):**
```python
# Query 1: Get story data, write to temp file
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
# ... query ...
with open('/tmp/stories.json', 'w') as f:
    json.dump(stories, f)
"

# Query 2: Process from file
python -c "
import json
with open('/tmp/stories.json') as f:
    stories = json.load(f)
# ... analysis ...
"
```

### Recommendation 6: Early Exit Check

**Priority:** Low
**Estimated Savings:** ~4,000 tokens when no stories

**Approach:** Check for approved stories before loading full skill.

**Current Flow:**
```
Load workflow prompt → Load slash command → Load skill → Query DB → (no stories) → Exit
```

**Optimized Flow:**
```
Load workflow prompt → Quick DB check → (no stories?) → Exit early
                                      → (has stories?) → Load skill → Continue
```

**Implementation:**
Add pre-check to workflow prompt:
```yaml
prompt: |
  First, check if there are approved stories:
  ```
  python -c "import sqlite3; conn = sqlite3.connect('.claude/data/story-tree.db');
  count = conn.execute('SELECT COUNT(*) FROM story_nodes WHERE status=\"approved\"').fetchone()[0];
  print(f'Approved stories: {count}'); conn.close()"
  ```

  If count is 0, output "✓ No approved stories available for planning" and exit.
  Otherwise, run /plan-story
```

---

## Implementation Plan

### Phase 1: Quick Wins (30 min)

1. **Create SKILL-CI.md** - Copy SKILL.md, remove interactive sections
2. **Update workflow** - Use SKILL-CI.md instead of full skill
3. **Add early exit check** - Pre-query for approved stories

**Expected Savings:** ~5,000 tokens / ~$0.15 per run

### Phase 2: Template Optimization (1 hour)

1. **Create compact TDD template** - Update Step 6 in SKILL-CI.md
2. **Test with sample story** - Verify plan is still actionable
3. **Update quality standards** - Adjust for compact format

**Expected Savings:** ~6,000 tokens / ~$0.18 per run

### Phase 3: Architecture Cleanup (2 hours)

1. **Consolidate prompt layers** - Remove slash command for CI
2. **Implement targeted file reading** - Add code landmarks reference
3. **Fix JSON handling** - Update database query patterns

**Expected Savings:** ~4,500 tokens / ~$0.14 per run

---

## Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Cost per run | $0.77 | $0.35 | 55% reduction |
| Plan file size | 1,339 lines | 500 lines | 63% reduction |
| Input tokens | ~28,000 | ~18,000 | 36% reduction |
| Output tokens | ~12,000 | ~4,000 | 67% reduction |

---

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/story-planning/SKILL-CI.md` | Create (new CI-optimized skill) |
| `.claude/skills/story-planning/SKILL.md` | Keep as-is for interactive use |
| `.github/workflows/daily-plan-story.yml` | Update to use SKILL-CI, add early exit |
| `.claude/commands/plan-story.md` | Add CI mode flag |
| `ai_docs/technical-reference.md` | Add code landmarks section |

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Compact plans less actionable | Medium | Test with actual implementation; keep full format as fallback |
| CI skill diverges from interactive | Low | Document differences; sync quarterly |
| Early exit misses edge cases | Low | Test with empty DB, single story, many stories |

---

## Appendix: Token Estimation Method

Token counts estimated using:
- ~4 characters per token (English text)
- ~3 characters per token (code with symbols)
- OpenAI tokenizer for validation on sample content
