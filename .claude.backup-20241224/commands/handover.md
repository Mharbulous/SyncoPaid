Generate a handover prompt for continuing this task in a new chat session.

## Required Sections

1. **Task Summary**: 1-2 sentences
2. **Current State**: Done vs remaining
3. **Key Files**: Paths only
4. **Failed Approaches** (CRITICAL): What was tried, why it failed, insights gained
5. **Working Constraints**: Discovered requirements, edge cases, gotchas
6. **Next Step**: Immediate action

## Output Format

```
[HANDOVER PROMPT]

**Task**: [brief description]

**Status**: [done / remaining]

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
