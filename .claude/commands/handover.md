Generate a handover prompt for continuing this task in a new chat session.

## Instructions

Analyze the current conversation context and create a concise handover prompt optimized for Sonnet 4.5. The prompt should enable a new chat to continue exactly where this one left off.

## What to Include

1. **Task Summary**: What is being worked on (1-2 sentences max)

2. **Current State**: Where exactly did we leave off? What's done vs remaining?

3. **Key Files**: List only the specific files that need attention (paths only, no explanations unless non-obvious)

4. **Failed Approaches** (CRITICAL): Document ALL debugging attempts or fixes that were tried and failed, including:
   - What was tried
   - Why it failed or what error occurred
   - Any insights gained from the failure

5. **Working Constraints**: Any discovered requirements, edge cases, or "gotchas" that aren't obvious from the code

6. **Next Step**: The immediate next action to take

## What to Omit

Since Sonnet 4.5 is highly knowledgeable, omit:
- Standard library/framework usage explanations
- Common design patterns that are self-evident from code
- Basic language syntax or conventions
- How standard tools work (git, pytest, npm, etc.)
- Obvious file purposes (e.g., don't explain that `config.py` handles configuration)
- Generic best practices

## Output Format

Output the handover prompt in a fenced code block so it can be easily copied:

```
[HANDOVER PROMPT]

**Task**: [brief description]

**Status**: [what's done / what remains]

**Files**:
- path/to/file1.py
- path/to/file2.py

**Failed Approaches**:
1. [approach] → [why it failed]
2. [approach] → [why it failed]

**Key Discoveries**:
- [non-obvious constraint or insight]

**Next Step**: [specific action]
```

Adjust the template as needed—some sections may be empty or need expansion based on the actual conversation context.
