# Xstory: Filter with Ancestry Display

## Problem
Status filter in Xstory hides nodes completely when unchecked. When filtering to show only "concept" status, nothing displays because concept nodes have non-concept parents (e.g., epic or approved parents).

## Required Behavior
When a status filter is applied:
1. Nodes matching filter: display normally
2. Ancestor nodes of matching nodes: display faded (half opacity) even if they don't match filter
3. Nodes not matching filter AND having no matching descendants: hide completely

## Source File
`dev-tools\xstory\xstory.py`

## Key Code Locations
- `_apply_filters()` at ~line 680: current filter logic using `tree.detach()`/`tree.reattach()`
- `_build_tree()` at ~line 645: builds tree from `self.nodes` dict
- `self.tree_items`: maps `node_id` → treeview item_id
- `StoryNode.parent_id` and `StoryNode.children`: parent-child relationships already built

## Implementation Approach
1. Compute set of visible node IDs (matching filter OR ancestor of matching node)
2. For nodes matching filter: normal display
3. For ancestor-only nodes: apply faded tag (configure tag with stipple or foreground color at 50% gray)
4. Use `tree.tag_configure()` to create 'faded' appearance
5. Detach nodes not in visible set

## Context from This Session
- Added right-click context menu for concept nodes (Approve/Reject/Wishlist/Revise)
- Added `StatusChangeDialog` class for notes input
- Added 'revising' status with goldenrod color
- All status change functionality working correctly

## Technical Note
tkinter Treeview doesn't support true opacity. Options:
- Use lighter foreground color for faded effect
- Use different font style (e.g., italic)
- Prepend visual indicator like "○" vs "●"
