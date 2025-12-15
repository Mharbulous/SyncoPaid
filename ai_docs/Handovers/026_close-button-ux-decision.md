# Handover: Feature Detail Window Close Button UX

## Context
User is implementing the xstory app (story-tree skill). Considering changing the X button on the Feature Detail window to close only that window and return to the main tree view, rather than closing the entire app.

## Decision Made
This is **standard, expected behavior** — not bad UX. We confirmed:
- X on child/secondary window → closes window, returns to parent (standard convention)
- X on main/root window → closes app
- Examples: file explorer properties dialogs, IDE tool windows, settings panels

## Implementation Recommendations
1. X on Feature Detail → return to tree view
2. Escape key should also close the detail window
3. Window title can reinforce hierarchy (e.g., "Feature: [name]")

## Key Files
- `src/syncopaid/skills/story-tree/` - xstory app location
- Look for window management code handling Feature Detail view

## Next Steps
Implement the close button behavior change if user wants to proceed.

## Branch
`claude/evaluate-close-button-ux-sZlHf`
