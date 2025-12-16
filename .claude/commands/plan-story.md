Create implementation plans for approved story-nodes using the story-planning skill.

## Arguments

$Arguments

## Instructions

Invoke the `story-planning` skill to create implementation plans for approved stories.

### Argument Handling

Parse the arguments to determine:

1. **Specific story ID(s)**: If arguments contain story IDs (e.g., "1.2.3", "1.8"), plan those specific stories
2. **Count modifier**: If arguments contain a number (e.g., "3", "5"), plan that many stories (max 5)
3. **No arguments**: Plan the single highest-priority approved story

**Examples:**
- `/plan-story` - Plan 1 highest-priority story
- `/plan-story 1.8.2` - Plan the specific story with ID 1.8.2
- `/plan-story 3` - Plan the top 3 highest-priority stories
- `/plan-story 1.2 1.3 1.4` - Plan these 3 specific stories
- `/plan-story 5` - Plan the top 5 stories (maximum allowed)

### Execution

1. Use the Skill tool to invoke the `story-planning` skill:

```
Skill(skill="story-planning")
```

2. After the skill prompt loads, execute the workflow with the parsed arguments:
   - If specific story IDs were provided, plan those stories in order
   - If a count was provided, plan that many top-priority stories sequentially
   - If no arguments, plan the single top-priority story

3. For multiple stories (count > 1 or multiple IDs):
   - Process each story sequentially
   - Create separate plan files for each
   - Update each story's status to `planned`
   - Provide a summary report at the end listing all plans created

### Constraints

- **Maximum 5 plans** per command invocation
- Only plan stories with `status = 'approved'`
- If a specified story ID doesn't exist or isn't approved, report the error and continue with remaining stories
- If fewer approved stories exist than requested, plan all available approved stories
