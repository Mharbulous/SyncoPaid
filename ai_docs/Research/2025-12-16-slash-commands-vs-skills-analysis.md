# Slash Commands vs Skills: Analysis & Recommendations

**Date:** 2025-12-16
**Focus:** Analyzing the division between `/plan-story` command and `story-planning` skill

## Executive Summary

After analyzing the current implementation, the **division is well-structured** with minor opportunities for improvement. The `/plan-story` command serves as a user-friendly argument parser and invocation wrapper, while the `story-planning` skill contains all the actual workflow logic. This follows best practices for Claude Code extensibility.

## General Principles: When to Use Each

### Slash Commands (.claude/commands/*.md)
**Purpose:** User-facing shortcuts and prompt expansion

**Best used for:**
- Simple prompt expansions (e.g., `/visualize` - 3 lines)
- User-friendly argument parsing before delegating to skills
- Orchestrating multiple skills or tools in a specific sequence
- Providing a memorable, typed interface for users

**Characteristics:**
- Lightweight markdown files
- Expand to prompts that Claude follows
- User types them (discoverability matters)
- Can invoke skills via Skill tool
- Typically < 100 lines

### Skills (.claude/skills/*/SKILL.md)
**Purpose:** Complex, autonomous workflows with quality enforcement

**Best used for:**
- Multi-step autonomous workflows (7+ steps)
- Complex logic with decision trees
- Quality checks and validation
- Database operations and analysis
- Workflows that need to be invoked by multiple commands OR natural language

**Characteristics:**
- Sophisticated with workflow steps, quality checks, common mistakes
- Can operate autonomously
- Invoked by skills OR natural language triggers
- Typically 100-400+ lines
- Self-documenting with rationale, examples, etc.

## Current Implementation Analysis

### Pattern Comparison Across Commands

| Command | Lines | Pattern | Assessment |
|---------|-------|---------|------------|
| `/visualize` | 3 | Pure delegation | ✅ Optimal - simple wrapper |
| `/plan-story` | 50 | Argument parser + delegation | ✅ Good - adds UX value |
| `/generate-stories` | 38 | GUI launcher + delegation | ✅ Good - orchestration |
| `/write-stories` | 80 | **Orchestrator with SQL queries** | ⚠️ Possible duplication |

### The `/plan-story` Command

**Current responsibilities:**
1. Parse user arguments (story IDs, count, or none)
2. Validate constraints (max 5 plans)
3. Invoke `story-planning` skill
4. Pass parsed arguments to skill

**Lines of code:** 50

**Assessment:** ✅ **Well-designed**

**Reasoning:**
- Provides user-friendly interface (`/plan-story 1.8.2` vs "invoke story-planning skill for 1.8.2")
- Argument parsing is legitimately UI layer logic
- No duplication with skill (skill contains all workflow logic)
- Enforces constraints before invocation
- Makes the feature discoverable via slash command autocomplete

### The `story-planning` Skill

**Current responsibilities:**
1. Database queries for approved stories
2. Dependency analysis
3. Priority scoring algorithm
4. Story selection
5. Codebase research
6. Plan generation with TDD structure
7. File writing and status updates
8. Quality validation

**Lines of code:** 418

**Assessment:** ✅ **Well-designed**

**Reasoning:**
- Contains all the actual workflow logic
- Can be invoked by command OR natural language ("plan a story")
- Autonomous operation with quality checks
- Comprehensive documentation
- No dependence on the slash command

## Comparison: `/write-stories` vs `brainstorm-story`

**Potential issue identified:** The `/write-stories` command contains SQL queries and orchestration logic (80 lines) that might belong in a skill.

**Current structure:**
```
/write-stories (80 lines)
├── SQL query to find nodes with capacity
├── Round-robin distribution logic
└── Invokes brainstorm-story skill
```

**Recommendation:** Consider moving the "find nodes with capacity" logic into the `brainstorm-story` skill, making `/write-stories` a simpler wrapper. This would follow the same pattern as `/plan-story`.

## Best Practice Patterns

### Pattern 1: Simple Wrapper (Recommended for most cases)
```markdown
# Command: /do-thing.md
Use the Skill tool to invoke the `thing-doer` skill.

Optional: Parse arguments and pass to skill.
```

**Examples:** `/visualize`, `/plan-story`

### Pattern 2: Orchestrator (Use sparingly)
```markdown
# Command: /complex-workflow.md
1. Launch GUI
2. Invoke skill A
3. Process results
4. Invoke skill B
5. Summarize
```

**Examples:** `/generate-stories` (launches GUI + delegates)

**When to use:** When the command genuinely orchestrates multiple independent tools/skills in a user-specific sequence that doesn't belong in a reusable skill.

### Pattern 3: Anti-pattern to Avoid
```markdown
# Command: /bad-example.md
1. Run complex SQL queries
2. Implement business logic
3. Generate content
4. Save to database
5. Oh, and maybe invoke a skill too
```

**Why it's bad:**
- Logic not reusable via natural language
- Duplication if a skill does similar things
- Hard to maintain (two places to update)
- Doesn't leverage skill's quality checks

## Recommendations

### For `/plan-story` + `story-planning`
**Status:** ✅ No changes needed

The current division is optimal:
- Command provides UX (argument parsing, constraints)
- Skill provides logic (workflow, quality, autonomy)
- No duplication
- Clear separation of concerns

### For `/write-stories` + `brainstorm-story`
**Status:** ⚠️ Consider refactoring

**Recommended change:**
1. Move "find nodes with capacity" logic into `brainstorm-story` skill
2. Add a "discovery mode" to the skill
3. Simplify `/write-stories` to just parse count/arguments and delegate

**Benefit:** Follows same pattern as `/plan-story`, reduces duplication, makes skill more autonomous

### General Guidelines

**Create a slash command when:**
- Users need a memorable shortcut
- Argument parsing adds UX value
- Orchestrating multiple skills/tools in a specific order
- The workflow is user-specific (not generalizable)

**Put logic in a skill when:**
- It's a multi-step autonomous workflow
- It needs quality checks and validation
- It should be accessible via natural language
- It contains business logic or algorithms
- It might be invoked by multiple commands

**Keep commands thin when:**
- A single skill does the heavy lifting
- The command is just improving UX/discoverability

## Conclusion

The `/plan-story` command and `story-planning` skill demonstrate excellent separation of concerns and are **not muddled**. The command serves as a user-friendly interface layer, while the skill contains all the autonomous workflow logic. This is the recommended pattern for Claude Code extensibility.

The only potential improvement area is `/write-stories`, which could be refactored to follow the same clean pattern.

## References

- Claude Code Documentation (implied from skill structure)
- Existing implementation analysis
- `/plan-story`: `.claude/commands/plan-story.md` (50 lines)
- `story-planning`: `.claude/skills/story-planning/SKILL.md` (418 lines)
