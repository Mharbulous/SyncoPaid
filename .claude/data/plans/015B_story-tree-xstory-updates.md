# Sub-Plan B: xstory.py Code Updates

## Overview

Update the xstory.py TUI to support the new `story` and `success_criteria` fields.

Parent plan: `015_story-tree-three-field-migration.md`
Depends on: `015A_story-tree-migration-script.md` (schema must be migrated first)

---

## TDD Tasks

### Task 1: Update StoryNode class

**File**: `dev-tools/xstory/xstory.py`

**Test approach**: Verify class instantiation with new fields

```python
# Add new fields to StoryNode.__init__
node = StoryNode(
    id='test', title='Test', status='approved',
    capacity=1, description='context',
    story='As a user, I want X, so that Y',
    success_criteria='- [ ] Criterion'
)
assert node.story == 'As a user, I want X, so that Y'
assert node.success_criteria == '- [ ] Criterion'
```

**Implementation**: Add `story: str = ''` and `success_criteria: str = ''` parameters and instance variables.

---

### Task 2: Update _load_nodes() SQL query

**File**: `dev-tools/xstory/xstory.py`

**Test approach**: Verify nodes load with new fields populated

```python
# After loading nodes, verify fields are populated
nodes = app._load_nodes()
sample_node = next((n for n in nodes if n.story), None)
assert sample_node is not None, "Should find at least one node with story field"
```

**Implementation**: Add `s.story, s.success_criteria` to SELECT clause and update StoryNode instantiation.

---

### Task 3: Update DetailView._update_detail() layout

**File**: `dev-tools/xstory/xstory.py`

**Test approach**: Visual verification in TUI

```bash
python dev-tools/xstory/xstory.py
# Navigate to a migrated story node
# Verify three sections appear: Story, Success Criteria, Description
```

**Implementation**:
- Add section header "Story" with `node.story` content
- Add section header "Success Criteria" with `node.success_criteria` content
- Keep existing "Description" section with `node.description`
- Keep "Notes" section unchanged

---

## Completion Criteria

- [ ] StoryNode class accepts new fields
- [ ] SQL query fetches story and success_criteria columns
- [ ] DetailView shows three separate content sections
- [ ] Notes section remains unchanged
- [ ] TUI launches and displays nodes correctly
