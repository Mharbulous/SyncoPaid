# Story Tree Structure Documentation

This document provides comprehensive documentation of the story tree JSON schema, field definitions, validation rules, and best practices.

## Schema Overview

The story tree is stored as a JSON file with a versioned schema:

```json
{
  "version": "1.0.0",
  "lastUpdated": "2025-12-11T00:00:00Z",
  "lastAnalyzedCommit": "29595a2",
  "root": { /* Node object */ }
}
```

## Top-Level Fields

### `version` (string, required)

Semantic version number of the schema format.

- **Format**: `MAJOR.MINOR.PATCH`
- **Current version**: `1.0.0`
- **Usage**: Allows backward compatibility checks and schema migrations

### `lastUpdated` (string, required)

ISO 8601 timestamp of when the tree was last modified.

- **Format**: `YYYY-MM-DDTHH:mm:ssZ`
- **Example**: `"2025-12-11T14:32:00Z"`
- **Usage**: Track tree changes over time, detect stale data

### `lastAnalyzedCommit` (string, optional)

Short git commit hash of the last commit that was analyzed for story matching.

- **Format**: Short commit hash (7+ characters)
- **Example**: `"29595a2"`
- **Usage**: Enables incremental commit analysis - only commits after this hash are analyzed on subsequent runs
- **When missing**: Falls back to full 30-day scan
- **Reset by**: "Rebuild story tree index" command, or when commit no longer exists (e.g., after rebase)

### `root` (object, required)

The root node of the story tree. See "Node Object Schema" below.

## Node Object Schema

Every node in the tree (including root) has the following structure:

```typescript
interface Node {
  id: string;                    // Required
  story: string;                 // Required
  description: string;           // Required
  capacity: number;              // Required
  status: Status;                // Required
  projectPath?: string;          // Optional
  implementedCommits?: string[]; // Optional
  lastImplemented?: string;      // Optional
  children: Node[];              // Required (can be empty array)
}

type Status =
  | "concept"
  | "planned"
  | "in-progress"
  | "implemented"
  | "deprecated"
  | "active"; // Only for root node
```

### Field Definitions

#### `id` (string, required)

Unique hierarchical identifier for the node.

- **Format**: Dotted notation: `"1.3.2.1"`
- **Root ID**: `"root"`
- **Rules**:
  - Must be unique across entire tree
  - Child IDs must start with parent ID
  - Numeric components only (except "root")
- **Examples**:
  - `"root"` - The root node
  - `"1.1"` - First child of root
  - `"1.3.2"` - Second child of third child of first child of root

#### `story` (string, required)

Short, human-readable title of the user story.

- **Length**: 3-100 characters recommended
- **Format**: Title case, concise description
- **Examples**:
  - `"Upload evidence files"`
  - `"Deduplicate identical uploads"`
  - `"Evidence management app (ListBot)"`
- **Best practices**:
  - Use action verbs for features ("Upload", "Analyze", "Organize")
  - Be specific and descriptive
  - Avoid jargon unless domain-specific

#### `description` (string, required)

Full user story in standard format.

- **Format**:
  ```
  As a [user role], I want [capability] so that [benefit]
  ```
- **Examples**:
  - `"As a lawyer, I want to upload discovery documents so that I can begin processing case evidence"`
  - `"As a paralegal, I want automatic deduplication so that I don't waste time on duplicate files"`
- **Best practices**:
  - Always use complete user story format
  - Be specific about user role
  - Focus on user benefit, not technical implementation
  - Keep under 200 characters when possible

#### `capacity` (number, required)

Target number of child nodes for this story.

- **Type**: Positive integer
- **Range**: 0-20 recommended
- **Default suggestions by level**:
  - Root: 10
  - Level 1 (apps): 5-10
  - Level 2 (major features): 5-8
  - Level 3 (capabilities): 2-5
  - Level 4+ (details): 2-3
- **Special case**: `0` means no children expected (leaf node)
- **Usage**: Drives autonomous story generation to fill gaps

#### `status` (enum, required)

Current implementation status of the story.

**Values**:

- **`"concept"`**: Idea exists but not approved for development
  - Use when: Brainstorming, considering options
  - Next state: `planned` (after approval)

- **`"planned"`**: Approved and scheduled for development
  - Use when: Added to backlog, prioritized
  - Next state: `in-progress` (when work starts)

- **`"in-progress"`**: Currently being implemented
  - Use when: Active development, commits detected
  - Next state: `implemented` (when complete)

- **`"implemented"`**: Completed and verified in production
  - Use when: Feature is live and working
  - Next state: N/A (terminal state, unless deprecated later)

- **`"deprecated"`**: No longer relevant or replaced
  - Use when: Feature removed, approach changed
  - Next state: N/A (terminal state)

- **`"active"`**: Special status for root node only
  - Use when: Root node (product vision is always "active")
  - Next state: N/A

**Status transition diagram**:
```
concept → planned → in-progress → implemented
                                      ↓
                                 deprecated
```

#### `projectPath` (string, optional)

Relative path to the project directory for this story.

- **Format**: Relative path from workspace root
- **Examples**:
  - `"./"` - Current project
  - `"./Bookkeeper"` - Multi-app workspace
  - `"./packages/auth"` - Monorepo structure
- **Usage**: Supports multi-app or monorepo architectures
- **Default**: Inherits from parent if not specified

#### `implementedCommits` (array of strings, optional)

Git commit hashes that implemented this story.

- **Format**: Array of short or full commit hashes
- **Example**: `["db1f3d91", "935bf082", "5711f94b"]`
- **Usage**:
  - Track implementation history
  - Link stories to code changes
  - Verify implementation status
- **Auto-populated**: By pattern matcher when commits match story keywords

#### `lastImplemented` (string, optional)

ISO 8601 timestamp of most recent implementation commit.

- **Format**: `YYYY-MM-DDTHH:mm:ssZ`
- **Example**: `"2025-12-10T18:45:00Z"`
- **Usage**: Track implementation recency, prioritize updates
- **Auto-populated**: By pattern matcher from commit dates

#### `children` (array, required)

Array of child Node objects.

- **Type**: `Node[]`
- **Can be empty**: `[]` for leaf nodes
- **Rules**:
  - Children must have IDs that extend parent ID
  - Children inherit `projectPath` from parent if not specified
- **Ordering**: Typically ordered by ID, but not required

## Validation Rules

### Structure Validation

```javascript
function validateNode(node, parentId = null) {
  const errors = []

  // Required fields
  if (!node.id) errors.push('Missing required field: id')
  if (!node.story) errors.push('Missing required field: story')
  if (!node.description) errors.push('Missing required field: description')
  if (typeof node.capacity !== 'number') errors.push('Missing or invalid field: capacity')
  if (!node.status) errors.push('Missing required field: status')
  if (!Array.isArray(node.children)) errors.push('Missing or invalid field: children')

  // ID validation
  if (node.id !== 'root' && parentId) {
    if (!node.id.startsWith(parentId + '.')) {
      errors.push(`Child ID "${node.id}" must start with parent ID "${parentId}."`)
    }
  }

  // Capacity validation
  if (node.capacity < 0) {
    errors.push('Capacity must be non-negative')
  }

  // Status validation
  const validStatuses = ['concept', 'planned', 'in-progress', 'implemented', 'deprecated', 'active']
  if (!validStatuses.includes(node.status)) {
    errors.push(`Invalid status: ${node.status}`)
  }

  // Root-specific validation
  if (node.id === 'root' && node.status !== 'active') {
    errors.push('Root node must have status "active"')
  }

  // Recursive validation
  for (const child of node.children) {
    errors.push(...validateNode(child, node.id))
  }

  return errors
}
```

### Semantic Validation

```javascript
function validateTreeSemantics(tree) {
  const warnings = []

  // Check for over-capacity nodes
  const allNodes = flattenTree(tree)
  for (const node of allNodes) {
    if (node.children.length > node.capacity) {
      warnings.push(`Node ${node.id} is over capacity: ${node.children.length}/${node.capacity}`)
    }
  }

  // Check for orphaned statuses
  for (const node of allNodes) {
    // Implemented nodes should have commits
    if (node.status === 'implemented' && (!node.implementedCommits || node.implementedCommits.length === 0)) {
      warnings.push(`Node ${node.id} is marked implemented but has no commits`)
    }

    // In-progress nodes should have some commits
    if (node.status === 'in-progress' && node.implementedCommits && node.implementedCommits.length > 3) {
      warnings.push(`Node ${node.id} is in-progress but has many commits (${node.implementedCommits.length}) - consider marking implemented`)
    }
  }

  // Check for duplicate IDs
  const ids = allNodes.map(n => n.id)
  const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index)
  if (duplicates.length > 0) {
    warnings.push(`Duplicate IDs found: ${duplicates.join(', ')}`)
  }

  return warnings
}
```

## Best Practices

### Capacity Guidelines

**Root level**:
- Start with capacity 5-10
- Represents major product areas or apps
- Only increase when you've validated multiple successful products

**Level 1 (Apps/Major Areas)**:
- Capacity 5-10 for complex apps
- Capacity 3-5 for focused apps
- Consider user workflows - each major workflow = 1-2 capacity

**Level 2 (Major Features)**:
- Capacity 5-8 for complex features (e.g., "Upload system")
- Capacity 3-5 for standard features (e.g., "Document search")
- Break down by user actions or system components

**Level 3+ (Specific Capabilities)**:
- Capacity 2-4 is typical
- Deeper levels should have smaller capacity
- At depth 5+, consider capacity 2-3 max

### Story Writing Guidelines

**Good story format** ✓:
```json
{
  "story": "Bulk document categorization",
  "description": "As a legal assistant, I want to categorize multiple documents at once so that I can organize case files efficiently without clicking each document",
  "capacity": 3
}
```

**Poor story format** ✗:
```json
{
  "story": "Improve UX",
  "description": "Make it better",
  "capacity": 10
}
```

**Why good matters**:
- Specific user role enables targeted design
- Clear capability enables testing
- Explicit benefit justifies priority
- Reasonable capacity enables planning

### Status Management

**Don't rush to "implemented"**:
- Only mark implemented when feature is **complete and working**
- If bugs remain, keep as "in-progress"
- "Implemented" means "users can use this successfully"

**Use "concept" liberally**:
- Brainstorm freely, mark as "concept"
- Promotes to "planned" when approved
- Safe to have many concepts (they don't clutter backlog)

**Track deprecated stories**:
- Don't delete deprecated nodes - mark them "deprecated"
- Preserves history and rationale
- Helps avoid repeating past mistakes

### Tree Organization

**Breadth vs. Depth**:
- Prefer breadth at higher levels (more app ideas)
- Prefer depth at lower levels (detailed capabilities)
- Avoid trees that are too deep (>6 levels gets unwieldy)

**Consistency**:
- Siblings should be at similar granularity
- If one level-2 node is "Upload", sibling shouldn't be "Add button to header" (too granular)
- Maintain consistent abstraction levels

**Leaf nodes**:
- Set `capacity: 0` for leaf nodes (no children expected)
- Leaf nodes should be actionable work items
- If a leaf node gets children, increase capacity from 0

## Migration and Versioning

### Version 1.0.0 → 2.0.0 (Future)

If breaking changes are needed, provide migration script:

```javascript
function migrateV1ToV2(v1Tree) {
  // Example: Add new required field
  const v2Tree = {
    version: "2.0.0",
    lastUpdated: new Date().toISOString(),
    root: migrateNodeV1ToV2(v1Tree.root)
  }
  return v2Tree
}

function migrateNodeV1ToV2(node) {
  return {
    ...node,
    // Add new V2 fields with defaults
    priority: 'medium', // New field in V2
    children: node.children.map(migrateNodeV1ToV2)
  }
}
```

## Complete Example

```json
{
  "version": "1.0.0",
  "lastUpdated": "2025-12-11T14:32:00Z",
  "lastAnalyzedCommit": "db1f3d91",
  "root": {
    "id": "root",
    "story": "SaaS Apps for lawyers",
    "description": "Build specialized SaaS applications for legal professionals",
    "capacity": 10,
    "status": "active",
    "children": [
      {
        "id": "1.1",
        "story": "Evidence management app (ListBot)",
        "description": "Help lawyers organize, deduplicate, and analyze case evidence",
        "capacity": 10,
        "status": "in-progress",
        "projectPath": "./",
        "children": [
          {
            "id": "1.1.1",
            "story": "Upload evidence files",
            "description": "As a lawyer, I want to upload discovery documents so that I can begin processing case evidence",
            "capacity": 5,
            "status": "implemented",
            "implementedCommits": ["db1f3d91", "935bf082"],
            "lastImplemented": "2025-12-10T18:45:00Z",
            "children": [
              {
                "id": "1.1.1.1",
                "story": "Drag-and-drop upload interface",
                "description": "As a lawyer, I want to drag and drop files so that I can quickly add evidence",
                "capacity": 0,
                "status": "implemented",
                "children": []
              }
            ]
          }
        ]
      },
      {
        "id": "1.2",
        "story": "Time tracking app",
        "description": "Automatic time tracking for lawyers to bill clients accurately",
        "capacity": 5,
        "status": "concept",
        "children": []
      }
    ]
  }
}
```

## Schema Diagram

```
┌─────────────────────────────────────────────┐
│ Tree Root                                   │
├─────────────────────────────────────────────┤
│ version: string                             │
│ lastUpdated: ISO8601                        │
│ root: Node                                  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Node                                        │
├─────────────────────────────────────────────┤
│ id: string (required)                       │
│ story: string (required)                    │
│ description: string (required)              │
│ capacity: number (required)                 │
│ status: Status (required)                   │
│ projectPath?: string (optional)             │
│ implementedCommits?: string[] (optional)    │
│ lastImplemented?: ISO8601 (optional)        │
│ children: Node[] (required, can be [])      │
└─────────────────┬───────────────────────────┘
                  │
                  │ 0..n children
                  ▼
         ┌────────┴────────┐
         │   Child Nodes   │
         │   (recursive)   │
         └─────────────────┘
```
