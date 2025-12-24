# Decompose Plan into Sub-Plans

Assess plan complexity and split into smaller sub-plans if needed.

**Arguments:**
- `$ARGUMENTS` - Path to the plan file (e.g., `.claude/data/plans/024_feature.md`)

---

## YOUR TASK

1. Read the plan file at `$ARGUMENTS` completely
2. Count the number of TDD tasks
3. Assess overall complexity based on:
   - Number of tasks (>2 is complex)
   - Cross-file dependencies
   - Integration complexity
   - Test complexity

## COMPLEXITY CLASSIFICATION

- **simple**: 1-2 tasks → execute directly
- **complex**: 3+ tasks → MUST decompose

## DECOMPOSITION RULES (MANDATORY)

If task_count > 2:
1. Split into sub-plans of 1-2 tasks each
2. Each sub-plan must be independently executable
3. Save sub-plans to `.claude/data/plans/`
4. First sub-plan executes this run, others queued for future runs

## HIERARCHICAL NAMING (CRITICAL)

Use hierarchical suffixes to maintain parent-child relationships:

| Level | Example | Pattern |
|-------|---------|---------|
| 0 (base) | `022_feature.md` | digits only |
| 1 | `022A_...`, `022B_...` | + uppercase letter |
| 2 | `022A1_...`, `022A2_...` | + number |
| 3 | `022A1a_...`, `022A1b_...` | + lowercase letter |
| 4 | `022A1a1_...`, `022A1a2_...` | + number |

To determine the correct suffix:
1. Parse the current plan's prefix (e.g., "024A" from "024A_timeline.md")
2. If prefix is just digits (024): add uppercase letter → 024A, 024B, 024C
3. If prefix ends with letter (024A): add number → 024A1, 024A2, 024A3
4. If prefix ends with number (024A1): add lowercase letter → 024A1a, 024A1b
5. If prefix ends with lowercase (024A1a): add number → 024A1a1, 024A1a2

## FILENAME COLLISION PREVENTION (CRITICAL)

BEFORE creating any sub-plans:
1. Run: `ls -1 .claude/data/plans/*.md` to see existing plans
2. Run: `ls -1 .claude/data/plans/executed/*.md` to see executed plans
3. Run: `ls -1 .claude/data/plans/decomposed/*.md` to see decomposed parent plans
4. Find ALL existing plans with the same parent prefix (in ALL folders)
5. Use the NEXT available suffix at the correct hierarchy level

## AUTOMATIC COMPLEXITY ESCALATION

Always flag as complex (even if ≤2 tasks) when plan involves:
- GUI/UI testing (tkinter, Qt, browser)
- Image processing (PIL, OpenCV)
- System package dependencies

## OUTPUT REQUIRED

Write to `.claude/skills/story-execution/ci-decompose-result.json`:

```json
{
  "complexity": "simple|complex",
  "task_count": 5,
  "execute_plan": ".claude/data/plans/016_configurable-idle-threshold.md",
  "sub_plans_created": [],
  "parent_moved": false,
  "notes": "Brief explanation"
}
```

If decomposed:
```json
{
  "complexity": "complex",
  "task_count": 12,
  "execute_plan": ".claude/data/plans/016A_idle-threshold-validation.md",
  "sub_plans_created": [
    ".claude/data/plans/016B_idle-threshold-integration.md",
    ".claude/data/plans/016C_idle-threshold-ui.md"
  ],
  "parent_moved": true,
  "notes": "Split into 3 sub-plans. Parent moved to decomposed/"
}
```

## IMPORTANT

If you create sub-plans:
1. Move the PARENT plan to `.claude/data/plans/decomposed/` folder
2. Create new sub-plan files with proper content
3. The `execute_plan` should be the FIRST sub-plan
4. VERIFY each file exists before putting it in the output
5. Set `parent_moved: true` in the JSON output

After writing the JSON, print a human-readable summary.
